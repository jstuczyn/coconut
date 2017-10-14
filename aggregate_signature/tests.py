""" tests """
from lib import setup
from lib import elgamal_keygen
from lib import keygen, sign, aggregate_sign, aggregate_keys, randomize, verify
from lib import prepare_blind_sign, blind_sign, elgamal_dec, prepare_blind_verify, blind_verify


# ==================================================
# test --  sign
# ==================================================
def test_sign():
	params = setup()

	# user parameters
	m = 10

	# signer 1
	(sk1, vk1) = keygen(params)
	sig1 = sign(params, sk1, m)

	# signer 2
	(sk2, vk2) = keygen(params)
	sig2 = sign(params, sk2, m)

	# affregate signatures
	sig = aggregate_sign(sig1, sig2)

	# randomize signature
	randomize(params, sig)

	# aggregate keys
	vk = aggregate_keys(vk1, vk2)

	# verify signature
	assert verify(params, vk, m, sig)


# ==================================================
# test -- private sign
# ==================================================
def test_private_sign():
	params = setup()
	(G, o, g1, h1, g2, e) = params

	# user parameters
	m = 5 # message
	(priv, pub) = elgamal_keygen(params) # El Gamal keypair
	
	# generate commitment and encryption for blind signature
	(cm, c, proof_s) = prepare_blind_sign(params, m, pub)

	# signer 1
	(sk1, vk1) = keygen(params)
	blind_sig1 = blind_sign(params, sk1, cm, c, pub, proof_s)
	(h, enc_sig1) = blind_sig1
	sig1 = (h, elgamal_dec(params, priv, enc_sig1))

	# signer 2
	(sk2, vk2) = keygen(params)
	blind_sig2 = blind_sign(params, sk2, cm, c, pub, proof_s)
	(h, enc_sig2) = blind_sig2
	sig2 = (h, elgamal_dec(params, priv, enc_sig2))

	# aggregate signatures
	sig = aggregate_sign(sig1, sig2)

	# randomize signature
	sig = randomize(params, sig)

	# aggregate keys
	vk = aggregate_keys(vk1, vk2)

	# generate kappa and proof of correctness
	(kappa, proof_v) = prepare_blind_verify(params, vk, m)

	# verify signature
	assert blind_verify(params, vk, kappa, sig, proof_v)




