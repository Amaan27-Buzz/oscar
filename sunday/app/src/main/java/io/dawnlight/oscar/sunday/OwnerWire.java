package io.dawnlight.oscar.sunday;

import java.security.*;
import java.security.spec.MGF1ParameterSpec;
import java.security.spec.PSSParameterSpec;
import java.util.Base64;

/** Same PSS wire contract for Android Keystore and the local JVM interoperability check. */
final class OwnerWire {
    static byte[] sign(PrivateKey key, byte[] payload) throws Exception {
        Signature signer = Signature.getInstance("RSASSA-PSS");
        signer.initSign(key);
        signer.setParameter(new PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1));
        signer.update(payload);
        return signer.sign();
    }
    public static void main(String[] args) throws Exception {
        // REFERENCE_JVM_ONLY: synthetic key, not Android Keystore or owner biometrics.
        if (args.length != 0) throw new IllegalArgumentException("reference pipe mode only");
        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(2048);
        KeyPair key = generator.generateKeyPair();
        System.out.println(Base64.getEncoder().encodeToString(key.getPublic().getEncoded()));
        String challenge = new java.io.BufferedReader(new java.io.InputStreamReader(System.in, java.nio.charset.StandardCharsets.UTF_8)).readLine();
        if (challenge == null || challenge.length() > 16000) throw new IllegalArgumentException("bounded reference challenge required");
        System.out.println(Base64.getEncoder().encodeToString(sign(key.getPrivate(), Base64.getDecoder().decode(challenge))));
    }
}
