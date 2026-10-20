package io.dawnlight.oscar.mobile

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/** Synthetic debug/review target. Never present in a release install. */
class CapabilityFixtureActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        check(android.os.Build.HARDWARE in setOf("ranchu", "goldfish")) { "Disposable emulator only" }
        val form = EditText(this).apply {
            id = R.id.capability_fixture_input; setHint(R.string.capability_fixture_hint)
            setText(savedInstanceState?.getString("draft") ?: intent.getStringExtra(android.content.Intent.EXTRA_TEXT).orEmpty())
        }
        val result = TextView(this).apply { id = R.id.capability_fixture_result; text = savedInstanceState?.getString("result") ?: getString(R.string.capability_fixture_empty) }
        val submit = Button(this).apply { id = R.id.capability_fixture_submit; setText(R.string.capability_fixture_review)
            setOnClickListener { result.text = getString(R.string.capability_fixture_result, form.text) } }
        setContentView(LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; addView(form); addView(submit); addView(result) })
    }
    override fun onSaveInstanceState(outState: Bundle) {
        outState.putString("draft", findViewById<EditText>(R.id.capability_fixture_input).text.toString())
        outState.putString("result", findViewById<TextView>(R.id.capability_fixture_result).text.toString())
        super.onSaveInstanceState(outState)
    }
}
