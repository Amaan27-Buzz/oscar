package io.dawnlight.oscar.mobile

import android.app.Activity
import android.hardware.biometrics.BiometricManager
import android.hardware.biometrics.BiometricPrompt
import android.os.CancellationSignal

/** Fresh task-bound confirmation. A successful biometric never creates a grant. */
class OwnerConfirmation(private val activity: Activity) {
    private var signal: CancellationSignal? = null
    fun cancel() { signal?.cancel(); signal = null }
    fun confirm(approval: Approval, accepted: () -> Unit, failed: () -> Unit) {
        cancel()
        val allowed = BiometricManager.Authenticators.BIOMETRIC_STRONG or BiometricManager.Authenticators.DEVICE_CREDENTIAL
        if (activity.getSystemService(BiometricManager::class.java).canAuthenticate(allowed) != BiometricManager.BIOMETRIC_SUCCESS) { failed(); return }
        val current = CancellationSignal()
        signal = current
        try {
        BiometricPrompt.Builder(activity).setTitle("Confirm ${approval.operation}")
            .setDescription(approval.description).setAllowedAuthenticators(allowed).build()
            .authenticate(current, activity.mainExecutor, object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    if (signal === current && !current.isCanceled) { signal = null; accepted() }
                }
                override fun onAuthenticationError(code: Int, reason: CharSequence) {
                    if (signal === current) { signal = null; failed() }
                }
            })
        } catch (_: Exception) { signal = null; failed() }
    }
}
