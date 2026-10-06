package io.dawnlight.oscar.mobile;

import android.app.KeyguardManager;
import android.content.Context;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import org.json.JSONObject;
import java.nio.charset.StandardCharsets;
import java.security.KeyPairGenerator;
import java.security.KeyStore;
import java.security.PrivateKey;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Android owns secret storage; Core owns pairing, scopes, expiry and revocation. */
final class SessionVault {
    private static final String VAULT = "oscar-session-v1", OWNER = "oscar-owner-v1";
    private final Context context;
    SessionVault(Context context) { this.context = context.getApplicationContext(); }

    private KeyStore keys() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        return store;
    }
    synchronized void save(JSONObject session) throws Exception {
        CoreClient.validateEndpoint(session.getString("url"));
        if (!session.getString("node_id").matches("[A-Za-z0-9_-]{1,80}") ||
            !session.getString("session_id").matches("[A-Za-z0-9_-]{1,80}") ||
            !session.getString("token").matches("[A-Za-z0-9_-]{20,200}"))
            throw new SecurityException("Invalid scoped session");
        KeyStore store = keys();
        if (!store.containsAlias(VAULT)) {
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(VAULT,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            generator.generateKey();
        }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, (SecretKey) keys().getKey(VAULT, null));
        JSONObject sealed = new JSONObject().put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
            .put("body", Base64.encodeToString(cipher.doFinal(session.toString().getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP));
        if (!context.getSharedPreferences("session", Context.MODE_PRIVATE).edit()
            .putString("sealed", sealed.toString()).commit())
            throw new SecurityException("Session persistence unverified");
    }
    synchronized JSONObject load() throws Exception {
        String value = context.getSharedPreferences("session", Context.MODE_PRIVATE).getString("sealed", null);
        if (value == null) return null;
        JSONObject sealed = new JSONObject(value);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, (SecretKey) keys().getKey(VAULT, null),
            new GCMParameterSpec(128, Base64.decode(sealed.getString("iv"), Base64.NO_WRAP)));
        return new JSONObject(new String(cipher.doFinal(Base64.decode(sealed.getString("body"), Base64.NO_WRAP)), StandardCharsets.UTF_8));
    }
    synchronized String publicIdentity() throws Exception {
        if (!context.getSystemService(KeyguardManager.class).isDeviceSecure())
            throw new SecurityException("Configure a device lock before owner enrollment");
        if (!keys().containsAlias(OWNER)) {
            KeyPairGenerator generator = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
            KeyGenParameterSpec.Builder specification = new KeyGenParameterSpec.Builder(OWNER, KeyProperties.PURPOSE_SIGN)
                .setKeySize(2048).setDigests(KeyProperties.DIGEST_SHA256)
                .setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PSS)
                .setUserAuthenticationRequired(true)
                .setUserAuthenticationParameters(15, KeyProperties.AUTH_BIOMETRIC_STRONG | KeyProperties.AUTH_DEVICE_CREDENTIAL)
                ;
            if (android.os.Build.VERSION.SDK_INT >= 35) specification.setMgf1Digests(KeyProperties.DIGEST_SHA256);
            generator.initialize(specification.build());
            generator.generateKeyPair();
        }
        return Base64.encodeToString(keys().getCertificate(OWNER).getPublicKey().getEncoded(), Base64.NO_WRAP);
    }
    synchronized String sign(String encoded) throws Exception {
        byte[] signature = OwnerWire.sign((PrivateKey) keys().getKey(OWNER, null),
            Base64.decode(encoded, Base64.NO_WRAP));
        return Base64.encodeToString(signature, Base64.NO_WRAP);
    }
    synchronized void forget() throws Exception {
        if (!context.getSharedPreferences("session", Context.MODE_PRIVATE).edit().clear().commit())
            throw new SecurityException("Local credential deletion unverified");
        KeyStore store = keys();
        store.deleteEntry(VAULT);
        store.deleteEntry(OWNER);
        // Local deletion is not remote revocation or a secure-erasure claim.
    }
}
