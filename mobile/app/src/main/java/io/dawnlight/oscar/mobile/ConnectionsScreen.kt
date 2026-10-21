package io.dawnlight.oscar.mobile

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.unit.dp
import org.json.JSONArray
import org.json.JSONObject

internal fun connectionChange(operation: String, id: String, value: String = "") = JSONObject().put("operation", operation).put("id", id).put("value", value)

@Composable fun ConnectionsScreen(session: CoreSession, state: MobileState) {
    val data = state.snapshot?.connections
    val available = state.canManage() && data != null && !data.truncated
    fun review(operation: String, id: String, value: String = "") = reviewChange(session, "management", connectionChange(operation, id, value))
    IllustratedIntro("Connections", "Your accounts. Your tools.", R.drawable.illustration_preferences, height = 144.dp)
    if (data == null) {
        StatusLabel("Connection readback unavailable")
        TextButton(onClick = session::refreshNow) { Text("Refresh from Core") }
        return
    }
    val identity = data.json().getJSONObject("identity")
    PreferenceGroup("OSCAR identity", flat = true) {
        Text(identity.optString("display_name", "OSCAR"), style = MaterialTheme.typography.titleLarge)
        identity.optString("operational_email").takeIf { it.isNotEmpty() }?.let { Text(it) }
        Text("Account identity, service permissions and access mode remain separate.", style = MaterialTheme.typography.bodySmall)
    }
    if (data.truncated) StatusLabel("Partial catalog. Refresh or use trusted Core setup before changing connections.")
    PreferenceGroup("Connected accounts", flat = true) {
        if (data.accounts().isEmpty()) Text("No accounts connected to this Core.")
        data.accounts().forEach { account -> key(account.getString("id")) {
            val id = account.getString("id")
            var alias by remember(state.epoch, account.getInt("generation")) { mutableStateOf(account.getString("alias")) }
            TactileSurface(Modifier.fillMaxWidth()) {
                FeatureRow(account.getString("alias"), "${account.getString("provider")} · ${account.getString("status")}", "Person")
                SupportingDetails("Identity & permissions") {
                    listOf("id", "identity_class", "subject", "tenant", "generation", "remote_revocation", "local_credentials").forEach { field ->
                        if (account.has(field) && !account.isNull(field)) Text("${field.replace('_', ' ')}: ${account.get(field)}", style = MaterialTheme.typography.bodySmall)
                    }
                    account.objects("services", 64).forEach { service ->
                        Text("${service.getString("id")}: ${service.getJSONArray("scopes").texts(128).joinToString()}", style = MaterialTheme.typography.bodySmall)
                        Text("Expiry: ${service.opt("expires_at")} · restrictions: ${service.optJSONArray("restrictions") ?: JSONArray()}", style = MaterialTheme.typography.bodySmall)
                    }
                }
                OscarField(alias, { alias = it.take(80) }, label = "Account name", modifier = Modifier.fillMaxWidth())
                TextButton(onClick = { review("rename_account", id, alias.trim()) }, enabled = available && alias.isNotBlank() && alias != account.getString("alias")) { Text("Review rename") }
                account.objects("services", 64).forEach { service ->
                    val serviceId = service.getString("id")
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        TextButton(onClick = { review("default_account", id, serviceId) }, enabled = available && account.getString("status") == "connected") { Text("Use for $serviceId") }
                        TextButton(onClick = { review("refresh_account", id, serviceId) }, enabled = available) { Text("Reconnect $serviceId") }
                    }
                }
                TextButton(onClick = { review("disconnect_account", id) }, enabled = available && account.getString("status") != "disconnected") { Text("Review disconnect") }
            }
        } }
    }
    SupportingDetails("Connect an account") {
        if (data.providers().isEmpty()) Text("Core has no configured provider applications. Register the provider application with your trusted Core before enrolling an account.", style = MaterialTheme.typography.bodySmall)
        data.providers().forEach { provider -> key(provider.getString("id")) {
            var alias by remember(state.epoch) { mutableStateOf("") }
            var scopes by remember(state.epoch) { mutableStateOf(emptySet<String>()) }
            var identityClass by remember(state.epoch) { mutableStateOf("owner-delegated") }
            Text("${provider.getString("provider")} · ${provider.getString("service")}", style = MaterialTheme.typography.titleMedium)
            OscarField(alias, { alias = it.take(80) }, label = "Account name", modifier = Modifier.fillMaxWidth())
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("owner-delegated" to "Your account", "oscar-owned" to "OSCAR's account").forEach { (value, label) -> FilterChip(selected = identityClass == value, onClick = { identityClass = value }, label = { Text(label) }) }
            }
            provider.getJSONArray("scopes").texts(128).forEach { scope ->
                Row { Checkbox(scope in scopes, { checked -> scopes = if (checked) scopes + scope else scopes - scope }); Text(scope, Modifier.padding(top = 12.dp)) }
            }
            OscarButton(onClick = { review("begin_account", provider.getString("id"), JSONObject().put("alias", alias.trim()).put("identity_class", identityClass).put("scopes", JSONArray(scopes.sorted())).toString()) },
                enabled = available && alias.isNotBlank() && scopes.isNotEmpty(), modifier = Modifier.fillMaxWidth().testTag("connectAccount")) { Text("Review account connection") }
        } }
        Text("After signed review, authorization opens in your browser. The native callback is bound to this device session and expires within ten minutes. Return to OSCAR to finish. If Android ends this process, start a fresh review. No connection is shown as ready until Core verifies it.", style = MaterialTheme.typography.bodySmall)
        TextButton(onClick = session::cancelAccountEnrollment) { Text("Cancel pending account enrollment") }
    }
    PreferenceGroup("Tools & MCP servers", flat = true) {
        if (data.plugins().isEmpty()) Text("No tool servers installed.")
        data.plugins().forEach { plugin -> key(plugin.getString("id")) {
            val id = plugin.getString("id")
            TactileSurface(Modifier.fillMaxWidth()) {
                FeatureRow(plugin.getString("name"), "${plugin.getString("health")} · ${if (plugin.getBoolean("enabled")) "enabled" else "disabled"}", "Devices")
                SupportingDetails("Server scope & recent activity") {
                    Text("${plugin.getString("transport")} · account ${plugin.getString("account_id")}", style = MaterialTheme.typography.bodySmall)
                    Text("Tool permissions: ${plugin.getJSONObject("permissions")}", style = MaterialTheme.typography.bodySmall)
                    Text("Discovered tools: ${plugin.objects("tools", 200).joinToString { it.getString("name") }}", style = MaterialTheme.typography.bodySmall)
                    plugin.optJSONArray("activity")?.let { activity -> (0 until minOf(activity.length(), 5)).forEach { Text(activity.get(it).toString(), style = MaterialTheme.typography.bodySmall) } }
                }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { review("connect_plugin", id) }, enabled = available && plugin.getBoolean("enabled")) { Text("Review connect") }
                    TextButton(onClick = { review(if (plugin.getBoolean("enabled")) "disable_plugin" else "enable_plugin", id) }, enabled = available) { Text(if (plugin.getBoolean("enabled")) "Disable" else "Enable") }
                    TextButton(onClick = { review("remove_plugin", id) }, enabled = available) { Text("Remove") }
                }
            }
        } }
    }
    SupportingDetails("Add a reviewed tool server") {
        var source by remember(state.epoch) { mutableStateOf("") }
        var trusted by remember(state.epoch, source) { mutableStateOf(false) }
        val registration = runCatching {
            require(source.toByteArray().size <= 20_000)
            JSONObject(source).also { require(it.keys().asSequence().toSet() == setOf("config", "reviewed")); require(it.getJSONObject("reviewed").length() in 1..200)
                val config = it.getJSONObject("config"); config.bounded("id", 128); require(config.optString("fixture_origin").isEmpty() && config.optString("credential_ref").isEmpty()) }
        }.getOrNull()
        val local = registration?.getJSONObject("config")?.optString("command")?.isNotEmpty() == true
        OscarField(source, { source = it.take(20_000) }, label = "Reviewed server configuration (JSON)", minLines = 4, modifier = Modifier.fillMaxWidth())
        Text("Include config and reviewed tool consequences. Credentials are provisioned through the connected account, never pasted here. Core validates server identity, account generation, permissions and reviewed files.", style = MaterialTheme.typography.bodySmall)
        if (local) Row { Checkbox(trusted, { trusted = it }); Text("I trust this local server to run with the Core host's user permissions, files and network.", Modifier.weight(1f).padding(top = 12.dp)) }
        OscarButton(onClick = { if (registration != null) review("register_plugin", registration.getJSONObject("config").getString("id"), registration.toString()) },
            enabled = available && registration != null && (!local || trusted), modifier = Modifier.fillMaxWidth()) { Text("Review add server") }
    }
    SupportingDetails("Revocation & verification") {
        Text("Disconnecting disables local use. Provider revocation and local credential deletion have separate readbacks and can remain unknown. Tool registration and connection are separate signed changes. Readiness reflects current Core discovery and health.", style = MaterialTheme.typography.bodySmall)
    }
}
