package io.dawnlight.oscar.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.Lifecycle
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private lateinit var session: CoreSession
    private lateinit var confirmation: OwnerConfirmation
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE)
        enableEdgeToEdge()
        session = ViewModelProvider(this)[CoreSession::class.java]
        confirmation = OwnerConfirmation(this)
        setContent { OscarApp(session, confirmation) }
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                session.start()
                try { awaitCancellation() } finally { confirmation.cancel(); session.stop() }
            }
        }
    }
}
