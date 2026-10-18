package io.dawnlight.oscar.mobile

import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.MGF1ParameterSpec
import java.security.spec.PSSParameterSpec
import java.security.spec.X509EncodedKeySpec
import java.util.Base64

/** EMULATED Keystore interoperability, without an Activity or owner authentication. */
class GridKeystoreTest {
    @Test fun exportGridIdentity() {
        assumeTrue("Disposable emulator required", android.os.Build.HARDWARE in setOf("ranchu", "goldfish"))
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val vault = SessionVault(context)
        val identity = vault.deviceIdentity()
        assertEquals(identity.toString(), vault.deviceIdentity().toString())
        val payload = "emulated-grid-proof".toByteArray()
        val public = KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(identity.getString("public_key"))))
        val verifier = Signature.getInstance("SHA256withRSA/PSS").apply {
            initVerify(public); setParameter(PSSParameterSpec("SHA-256", "MGF1", MGF1ParameterSpec.SHA256, 32, 1)); update(payload)
        }
        assertTrue(verifier.verify(Base64.getDecoder().decode(vault.signDevice(payload))))
        File(context.filesDir, "d2-device-identity.json").writeText(identity.toString())
    }
}
