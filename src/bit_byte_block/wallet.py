"""Bitcoin keypair generation for solo mining ingress."""

from __future__ import annotations

import hashlib
import secrets

from cryptography.hazmat.primitives.asymmetric.ec import SECP256K1, derive_private_key
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def _sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _hash160(data: bytes) -> bytes:
    """SHA-256 then RIPEMD-160 (standard Bitcoin hash160)."""
    sha256_digest = hashlib.sha256(data).digest()
    return hashlib.new("ripemd160", sha256_digest).digest()


# ---------------------------------------------------------------------------
# Bech32 (BIP173) — P2WPKH native SegWit address encoding
# ---------------------------------------------------------------------------


def _bech32_polymod(values: list[int]) -> int:
    gen = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if (b >> i) & 1 else 0
    return chk


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def _convertbits(data: bytes, frombits: int, tobits: int) -> list[int]:
    acc, bits, ret = 0, 0, []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if bits:
        ret.append((acc << (tobits - bits)) & maxv)
    return ret


def _bech32_encode(hrp: str, witver: int, witprog: bytes) -> str:
    data = [witver] + _convertbits(witprog, 8, 5)
    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data + [0] * 6) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(_BECH32_CHARSET[d] for d in data + checksum)


# ---------------------------------------------------------------------------
# Base58Check — WIF private key encoding / decoding
# ---------------------------------------------------------------------------


def _base58check_encode(payload: bytes) -> str:
    full = payload + _sha256d(payload)[:4]
    leading_zeros = len(full) - len(full.lstrip(b"\x00"))
    n = int.from_bytes(full, "big")
    digits: list[str] = []
    while n > 0:
        n, rem = divmod(n, 58)
        digits.append(chr(_BASE58_ALPHABET[rem]))
    return "1" * leading_zeros + "".join(reversed(digits))


def _base58check_decode(s: str) -> bytes:
    """Decode a base58check string and return the payload (without checksum).

    Raises ValueError if the checksum does not match.
    """
    _alpha = _BASE58_ALPHABET.decode("ascii")
    n = 0
    for ch in s:
        n = n * 58 + _alpha.index(ch)
    # Only *leading* '1' characters map to leading 0x00 bytes; interior '1'
    # characters are just the base58 digit zero and are already captured in n.
    leading = len(s) - len(s.lstrip("1"))
    nbytes = (n.bit_length() + 7) // 8 if n > 0 else 0
    full = b"\x00" * leading + n.to_bytes(nbytes, "big")
    payload, checksum = full[:-4], full[-4:]
    if _sha256d(payload)[:4] != checksum:
        raise ValueError("base58check checksum mismatch")
    return payload


def _wif_to_privkey(wif: str) -> bytes:
    """Decode a compressed mainnet WIF string to the raw 32-byte private key."""
    payload = _base58check_decode(wif)
    if len(payload) != 34 or payload[0] != 0x80 or payload[-1] != 0x01:
        raise ValueError("not a compressed mainnet WIF key")
    return payload[1:33]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_keypair(wif: str, address: str) -> None:
    """Verify that wif round-trips back to address.

    Decodes the WIF to the raw private key, re-derives the compressed public
    key, recomputes the P2WPKH address, and asserts it matches the supplied
    address.  Raises ValueError if there is any mismatch, indicating a bug in
    the encoding pipeline.
    """
    raw = _wif_to_privkey(wif)
    private_key = derive_private_key(int.from_bytes(raw, "big"), SECP256K1())
    pub_key = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint)
    derived = _bech32_encode("bc", 0, _hash160(pub_key))
    if derived != address:
        raise ValueError(
            f"keypair verification failed: WIF re-derives to {derived!r}, expected {address!r}"
        )


def generate_keypair() -> tuple[str, str]:
    """Generate a secp256k1 keypair and derive a native SegWit P2WPKH address.

    Returns:
        (wif, address) where:
        - wif: compressed mainnet WIF private key (starts with K or L)
        - address: bech32 P2WPKH mainnet address (starts with bc1q)

    Raises ValueError if the internal round-trip verification fails.
    """
    while True:
        raw = secrets.token_bytes(32)
        key_int = int.from_bytes(raw, "big")
        if 0 < key_int < _SECP256K1_ORDER:
            break

    private_key = derive_private_key(key_int, SECP256K1())
    pub_key = private_key.public_key().public_bytes(Encoding.X962, PublicFormat.CompressedPoint)

    address = _bech32_encode("bc", 0, _hash160(pub_key))
    wif = _base58check_encode(b"\x80" + raw + b"\x01")

    verify_keypair(wif, address)

    return wif, address
