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
    private static final String VAULT = "oscar-session-v1", OWNER = "oscar-owner-v1", DEVICE = "oscar-device-v2";
    private final Context context;
    SessionVault(Context context) { this.context = context.getApplicationContext(); }

    private KeyStore keys() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        return store;
    }
    private SecretKey secretKey() throws Exception {
        KeyStore store = keys();
        if (!store.containsAlias(VAULT)) {
            KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            generator.init(new KeyGenParameterSpec.Builder(VAULT,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setKeySize(256).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
            generator.generateKey();
        }
        return (SecretKey) keys().getKey(VAULT, null);
    }
    synchronized void save(JSONObject session) throws Exception {
        CoreClient.validateEndpoint(session.getString("url"));
        if (!session.getString("node_id").matches("[A-Za-z0-9_-]{1,80}") ||
            !session.getString("session_id").matches("[A-Za-z0-9_-]{1,80}") ||
            !session.getString("token").matches("[A-Za-z0-9_-]{20,200}"))
            throw new SecurityException("Invalid scoped session");
        if (session.optInt("version", 1) == 2 &&
            (!session.getString("core_id").matches("[A-Za-z0-9_-]{1,80}") ||
             session.getLong("expires_at_ms") <= System.currentTimeMillis() || session.getJSONArray("scopes").length() > 64))
            throw new SecurityException("Invalid Grid session");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, secretKey());
        JSONObject sealed = new JSONObject().put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
            .put("body", Base64.encodeToString(cipher.doFinal(session.toString().getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP));
        if (!context.getSharedPreferences("session", Context.MODE_PRIVATE).edit()
            .putString("sealed", sealed.toString()).remove("draft").remove("history").remove("privacy_pending").commit())
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
    synchronized void saveDraft(String text, String binding) throws Exception { saveDraft(text, binding, suppressed(binding)); }
    synchronized void saveDraft(String text, String binding, boolean hidden) throws Exception {
        if (text.length() > 1000) throw new SecurityException("Draft exceeds boundary");
        JSONObject current = load();
        if (!(current == null ? "unpaired" : new CoreClient(current).binding()).equals(binding)) throw new SecurityException("Draft source changed");
        var edit = context.getSharedPreferences("session", Context.MODE_PRIVATE).edit();
        if (hidden) edit.putString("privacy_pending", binding); else edit.remove("privacy_pending");
        if (text.isEmpty()) { if (!edit.remove("draft").commit()) throw new SecurityException("Private recovery deletion unverified"); return; }
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, secretKey());
        cipher.updateAAD(binding.getBytes(StandardCharsets.UTF_8));
        JSONObject sealed = new JSONObject().put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
            .put("body", Base64.encodeToString(cipher.doFinal(text.getBytes(StandardCharsets.UTF_8)), Base64.NO_WRAP));
        if (!edit.putString("draft", sealed.toString()).commit()) throw new SecurityException("Draft persistence unverified");
    }
    synchronized String loadDraft(String binding) throws Exception {
        String value = context.getSharedPreferences("session", Context.MODE_PRIVATE).getString("draft", null);
        if (value == null) return "";
        JSONObject sealed = new JSONObject(value);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, (SecretKey) keys().getKey(VAULT, null),
            new GCMParameterSpec(128, Base64.decode(sealed.getString("iv"), Base64.NO_WRAP)));
        cipher.updateAAD(binding.getBytes(StandardCharsets.UTF_8));
        String text = new String(cipher.doFinal(Base64.decode(sealed.getString("body"), Base64.NO_WRAP)), StandardCharsets.UTF_8);
        if (text.length() > 1000) throw new SecurityException("Draft exceeds boundary");
        return text;
    }
    synchronized boolean suppressed(String binding) {
        return binding.equals(context.getSharedPreferences("session", Context.MODE_PRIVATE).getString("privacy_pending", null));
    }
    synchronized void saveHistory(JSONObject history, String binding) throws Exception {
        byte[] bytes = history.toString().getBytes(StandardCharsets.UTF_8);
        if (bytes.length > 262144) throw new SecurityException("History cache exceeds boundary");
        JSONObject current = load();
        if (current == null || !new CoreClient(current).binding().equals(binding)) throw new SecurityException("History source changed");
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, secretKey()); cipher.updateAAD(binding.getBytes(StandardCharsets.UTF_8));
        JSONObject sealed = new JSONObject().put("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP))
            .put("body", Base64.encodeToString(cipher.doFinal(bytes), Base64.NO_WRAP));
        if (!context.getSharedPreferences("session", Context.MODE_PRIVATE).edit().putString("history", sealed.toString()).commit())
            throw new SecurityException("History persistence unverified");
    }
    synchronized JSONObject loadHistory(String binding) throws Exception {
        String saved = context.getSharedPreferences("session", Context.MODE_PRIVATE).getString("history", null);
        if (saved == null) return null;
        JSONObject sealed = new JSONObject(saved);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, (SecretKey) keys().getKey(VAULT, null),
            new GCMParameterSpec(128, Base64.decode(sealed.getString("iv"), Base64.NO_WRAP)));
        cipher.updateAAD(binding.getBytes(StandardCharsets.UTF_8));
        return new JSONObject(new String(cipher.doFinal(Base64.decode(sealed.getString("body"), Base64.NO_WRAP)), StandardCharsets.UTF_8));
    }
    synchronized void clearHistory() throws Exception {
        if (!context.getSharedPreferences("session", Context.MODE_PRIVATE).edit().remove("history").commit())
            throw new SecurityException("History cache removal unverified");
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
    synchronized JSONObject deviceIdentity() throws Exception {
        if (!keys().containsAlias(DEVICE)) {
            KeyPairGenerator generator = KeyPairGenerator.getInstance(KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
            KeyGenParameterSpec.Builder specification = new KeyGenParameterSpec.Builder(DEVICE, KeyProperties.PURPOSE_SIGN)
                .setKeySize(2048).setDigests(KeyProperties.DIGEST_SHA256)
                .setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PSS);
            if (android.os.Build.VERSION.SDK_INT >= 35) specification.setMgf1Digests(KeyProperties.DIGEST_SHA256);
            generator.initialize(specification.build());
            generator.generateKeyPair();
        }
        var preferences = context.getSharedPreferences("session", Context.MODE_PRIVATE);
        String installation = preferences.getString("installation_id", null);
        if (installation == null) {
            installation = java.util.UUID.randomUUID().toString();
            if (!preferences.edit().putString("installation_id", installation).commit())
                throw new SecurityException("Installation persistence unverified");
        }
        return new JSONObject().put("installation_id", installation)
            .put("public_key", Base64.encodeToString(keys().getCertificate(DEVICE).getPublicKey().getEncoded(), Base64.NO_WRAP));
    }
    synchronized String signDevice(byte[] payload) throws Exception {
        return Base64.encodeToString(OwnerWire.sign((PrivateKey) keys().getKey(DEVICE, null), payload), Base64.NO_WRAP);
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
        store.deleteEntry(DEVICE);
        // Local deletion is not remote revocation or a secure-erasure claim.
    }
}
