package io.dawnlight.oscar.sunday;

import android.Manifest;
import android.app.*;
import android.app.role.RoleManager;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.content.res.ColorStateList;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.*;
import android.provider.Settings;
import android.service.voice.VoiceInteractionService;
import android.text.InputType;
import android.view.*;
import android.webkit.WebView;
import android.widget.*;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

/** One native owner surface. All reasoning, tasks, memory and authority remain in Core. */
public final class MainActivity extends Activity {
    private static final int INK = Color.rgb(26,27,24), PAPER = Color.rgb(245,241,231);
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private final AtomicInteger generation = new AtomicInteger();
    private SessionVault vault;
    private CoreClient core;
    private LinearLayout surface, tasks;
    private TextView status, response;
    private EditText input;
    private WebView orb;
    private volatile boolean foreground;
    private CancellationSignal confirmation;
    private JSONObject snapshot;
    private String interactionMessage;
    private long observedElapsed;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final Runnable refresh = new Runnable() {
        @Override public void run() { if (foreground) { refresh(); handler.postDelayed(this, 15000); } }
    };
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
    private TextView text(String value, int size) {
        TextView view = new TextView(this);
        view.setText(value); view.setTextColor(INK); view.setTextSize(size);
        view.setPadding(0, dp(8), 0, dp(8)); view.setSaveEnabled(false);
        return view;
    }
    private Button button(String value, View.OnClickListener action) {
        Button view = new Button(this); view.setText(value); view.setAllCaps(false);
        view.setMinHeight(dp(48)); view.setTextColor(INK); view.setOnClickListener(action);
        GradientDrawable shape=new GradientDrawable();shape.setColor(Color.rgb(250,247,239));shape.setCornerRadius(dp(12));
        view.setBackground(new RippleDrawable(ColorStateList.valueOf(Color.rgb(221,215,202)),shape,null));
        view.setStateListAnimator(null);
        return view;
    }
    private EditText field(String hint, boolean secret) {
        EditText view = new EditText(this); view.setHint(hint); view.setTextColor(INK);
        view.setMinHeight(dp(48)); view.setSingleLine(); view.setSaveEnabled(false);
        if (secret) view.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        return view;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state); vault = new SessionVault(this);
        getWindow().setStatusBarColor(PAPER); getWindow().setNavigationBarColor(PAPER);
        ScrollView scroll = new ScrollView(this);
        surface = new LinearLayout(this); surface.setOrientation(LinearLayout.VERTICAL);
        surface.setBackgroundColor(PAPER); surface.setPadding(dp(24), dp(20), dp(24), dp(24));
        surface.setOnApplyWindowInsetsListener((view, insets) -> {
            var bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime());
            view.setPadding(dp(24)+bars.left, dp(20)+bars.top, dp(24)+bars.right, dp(24)+bars.bottom);
            return insets;
        });
        scroll.addView(surface); setContentView(scroll);
        LinearLayout header = new LinearLayout(this); header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = text("OSCAR", 24); title.setTypeface(null, Typeface.BOLD);
        header.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
        header.addView(button("Controls", view -> controls())); surface.addView(header);
        orb = new WebView(this); orb.setBackgroundColor(Color.TRANSPARENT);
        orb.getSettings().setJavaScriptEnabled(false); orb.getSettings().setAllowFileAccess(false);
        orb.getSettings().setAllowContentAccess(false); orb.getSettings().setBlockNetworkLoads(true);
        orb.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        try (var art = getAssets().open("oscar-orb.svg")) {
            java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            byte[] block = new byte[8192]; int count;
            while ((count=art.read(block))!=-1) bytes.write(block,0,count);
            String encoded = android.util.Base64.encodeToString(bytes.toByteArray(), android.util.Base64.NO_WRAP);
            orb.loadDataWithBaseURL(null, "<html style='height:100%'><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='height:100%;margin:0;background:transparent'><img alt='OSCAR' style='width:100%;height:100%;object-fit:contain' src='data:image/svg+xml;base64,"+encoded+"'></body></html>", "text/html", "UTF-8", null);
        } catch (Exception unavailable) { orb.setVisibility(View.GONE); }
        LinearLayout.LayoutParams artwork = new LinearLayout.LayoutParams(dp(144), dp(144));
        artwork.gravity = Gravity.CENTER_HORIZONTAL; artwork.topMargin=dp(32); artwork.bottomMargin=dp(20);
        surface.addView(orb, artwork);
        status=text("Not connected",22); status.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
        response=text("Sunday shares OSCAR’s tasks and permissions. Connect to your trusted Core to continue.",16);
        surface.addView(status); surface.addView(response);
        input=field("Write to OSCAR",false); input.setSingleLine(false); input.setMaxLines(4);
        input.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(1000)});
        surface.addView(input);
        Button continueButton=button("Continue",view -> {
            if (core==null) { connect(); return; }
            String value=input.getText().toString(); if (value.trim().isEmpty()) return;
            try { request("text",new JSONObject().put("text",value),result -> {
                input.setText(""); interactionMessage=result.optString("message","Waiting for your approval."); response.setText(interactionMessage); refresh();
            }); } catch (JSONException invalid) { showFailure(); }
        });
        GradientDrawable primary=new GradientDrawable();primary.setColor(INK);primary.setCornerRadius(dp(12));
        continueButton.setBackground(new RippleDrawable(ColorStateList.valueOf(Color.rgb(80,81,77)),primary,null));
        continueButton.setTextColor(Color.rgb(255,253,248));surface.addView(continueButton);
        tasks=new LinearLayout(this); tasks.setOrientation(LinearLayout.VERTICAL); surface.addView(tasks);
        try { JSONObject session=vault.load(); if (session!=null) core=new CoreClient(session); }
        catch (Exception unavailable) { response.setText("Saved pairing is unavailable. Reconnect from your trusted Core."); }
    }
    interface Result { void accept(JSONObject result) throws Exception; }
    private void request(String operation, JSONObject payload, Result result) {
        if (core==null || !foreground) { status.setText("Not connected"); return; }
        int turn=generation.get(); CoreClient client=core;
        String requestId=UUID.randomUUID().toString();
        network.execute(() -> {
            if (!foreground || generation.get()!=turn) return;
            long started=SystemClock.elapsedRealtime();
            try {
                JSONObject value=client.call(operation,payload,requestId);
                value.put("_request_started_elapsed_ms",started);
                runOnUiThread(() -> { if (!foreground || generation.get()!=turn) return;
                    try { result.accept(value); } catch (Exception unavailable) { showFailure(); }
                });
            } catch (Exception unavailable) { runOnUiThread(() -> { if (foreground && generation.get()==turn) showFailure(); }); }
        });
    }
    private void showFailure() {
        status.setText("Connection unavailable"); orb.setAlpha(0.45f); tasks.removeAllViews();
        response.setText("No new action is confirmed. Refresh Core state before trying again.");
    }
    private void refresh() {
        if (core==null) return;
        request("snapshot",new JSONObject(),value -> {
            snapshot=value; observedElapsed=SystemClock.elapsedRealtime();
            status.setText("Connected to Core"); orb.setAlpha(1f);
            JSONArray rows=value.getJSONArray("tasks"); tasks.removeAllViews();
            response.setText(interactionMessage!=null?interactionMessage:
                (rows.length()==0?"Nothing is waiting for your decision. Text currently supports permitted integer addition.":
                "Your task state is shared with Core. Review a decision or continue with permitted integer addition."));
            if (rows.length()==0) return;
            for (int i=0;i<rows.length();i++) {
                JSONObject task=rows.getJSONObject(i);
                LinearLayout row=new LinearLayout(this); row.setOrientation(LinearLayout.VERTICAL);
                row.setPadding(0,dp(20),0,dp(12));
                row.addView(text(task.getString("description"),18));
                row.addView(text(task.getString("state")+" · "+task.getString("node_status"),14));
                if(task.has("value")) row.addView(text("Result · "+task.getString("value"),16));
                LinearLayout actions=new LinearLayout(this);
                if(getResources().getConfiguration().fontScale>1.2f) actions.setOrientation(LinearLayout.VERTICAL);
                actions.addView(button("Inspect",v -> inspect(task)));
                if ("planned".equals(task.getString("state"))) actions.addView(button("Approve",v -> decision("approve",task)));
                if (!java.util.List.of("verified","failed","cancelled").contains(task.getString("state")))
                    actions.addView(button("Cancel",v -> decision("cancel",task)));
                row.addView(actions); tasks.addView(row);
            }
        });
    }
    private void inspect(JSONObject task) {
        try { request("inspect",new JSONObject().put("task_id",task.getString("task_id")),value ->
            new AlertDialog.Builder(this).setTitle(value.getString("description"))
                .setMessage("State: "+value.getString("state")+"\nExecutor: "+value.getString("node_status")+
                    (value.has("value")?"\nResult: "+value.getString("value"):"")+"\nVerification evidence: "+value.getJSONArray("evidence_ids").length())
                .setPositiveButton("Close",null).show()); }
        catch (Exception invalid) { showFailure(); }
    }
    private void decision(String operation,JSONObject task) {
        try { request("challenge",new JSONObject().put("operation",operation).put("task_id",task.getString("task_id")),
            challenge -> confirm(challenge,value -> { interactionMessage=value.has("value")?"The result is "+value.getString("value")+".":"Core reports "+value.optString("state","a response")+".";response.setText(interactionMessage); refresh(); })); }
        catch (Exception invalid) { showFailure(); }
    }
    private void confirm(JSONObject challenge,Result completed) throws Exception {
        if (!foreground) return;
        confirmation=new CancellationSignal(); int turn=generation.get();
        new BiometricPrompt.Builder(this).setTitle(challenge.getString("operation")+" · OSCAR")
            .setDescription(challenge.getString("description"))
            .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG | BiometricManager.Authenticators.DEVICE_CREDENTIAL)
            .build().authenticate(confirmation,getMainExecutor(),new BiometricPrompt.AuthenticationCallback() {
                @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                    if (!foreground || generation.get()!=turn) return;
                    try {
                        JSONObject signed=new JSONObject().put("challenge_id",challenge.getString("challenge_id"))
                            .put("signature",vault.sign(challenge.getString("signing_payload")));
                        request("complete",signed,completed);
                    } catch (Exception unavailable) { response.setText("Owner signing is unavailable. No action is confirmed."); }
                }
                @Override public void onAuthenticationError(int code,CharSequence reason) {
                    response.setText("Confirmation cancelled or unavailable. No action is confirmed.");
                }
            });
        // Device-credential path uses a 15-second Keystore authorization window, not per-use CryptoObject proof.
    }
    private void connect() {
        LinearLayout form=new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(dp(24),0,dp(24),0);
        EditText origin=field("Trusted HTTPS Core origin",false),node=field("Paired node ID",false),session=field("Session ID",false),token=field("Scoped session token",true);
        form.addView(origin);form.addView(node);form.addView(session);form.addView(token);
        new AlertDialog.Builder(this).setTitle("Connect this embodiment").setView(form)
            .setMessage("Enroll the public owner identity from your trusted Core first. This does not grant Android permissions.")
            .setNegativeButton("Cancel",null).setPositiveButton("Connect",(dialog,which)-> {
                try { JSONObject value=new JSONObject().put("url",origin.getText().toString()).put("node_id",node.getText().toString())
                    .put("session_id",session.getText().toString()).put("token",token.getText().toString());
                    vault.save(value);core=new CoreClient(value);generation.incrementAndGet();refresh();
                } catch (Exception unavailable) { response.setText("Pairing could not be saved. Check the trusted origin and scoped session."); }
            }).show();
    }
    private void controls() {
        String[] choices={"Connection Grid","Connect Core","Owner public identity","Android permissions","Exposed notification replies","Disconnect locally"};
        new AlertDialog.Builder(this).setTitle("Owner controls").setItems(choices,(dialog,index)-> {
            if (index==0) grid();
            if (index==1) connect();
            if (index==2) {
                try { TextView identity=text(vault.publicIdentity(),12);identity.setTextIsSelectable(true);
                    new AlertDialog.Builder(this).setTitle("Enroll from trusted Core").setView(identity)
                        .setMessage("Public device signing key. No owner authority is minted here.")
                        .setPositiveButton("Close",null).show(); }
                catch (Exception unavailable) { response.setText("Owner key unavailable. Configure a device lock and verify platform support."); }
            }
            if (index==3) permissions();
            if (index==4) notifications();
            if (index==5) { try { vault.forget();core=null;snapshot=null;generation.incrementAndGet();tasks.removeAllViews();
                status.setText("Disconnected locally");orb.setAlpha(0.45f);response.setText("Local session cleared. Revoke the device from Core separately."); }
                catch (Exception unavailable) { response.setText("Local credential deletion is unverified."); } }
        }).show();
    }
    private void grid() {
        if (snapshot==null) { response.setText("Refresh your trusted Core connection first."); return; }
        try {
            StringBuilder value=new StringBuilder();JSONArray nodes=snapshot.getJSONArray("nodes");
            for(int i=0;i<nodes.length();i++) { JSONObject node=nodes.getJSONObject(i);
                value.append(node.getString("role")).append(" · ").append(node.getString("status")).append('\n'); }
            if(SystemClock.elapsedRealtime()-observedElapsed>30000) value.append("This snapshot is stale. Refresh before acting.");
            new AlertDialog.Builder(this).setTitle("Connection Grid").setMessage(value.toString())
                .setPositiveButton("Refresh",(d,w)->refresh()).setNegativeButton("Close",null).show();
        } catch(Exception invalid) { showFailure(); }
    }
    private void permissions() {
        LinearLayout content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(24),0,dp(24),0);
        boolean assistant=VoiceInteractionService.isActiveService(this,new ComponentName(this,AssistantService.class));
        content.addView(text("Assistant: "+(assistant?"selected":"not selected")+"\nMicrophone: "+
            (checkSelfPermission(Manifest.permission.RECORD_AUDIO)==PackageManager.PERMISSION_GRANTED?"granted":"not granted")+
            "\nNotification access: "+(getSystemService(NotificationManager.class).isNotificationListenerAccessGranted(
                new ComponentName(this,NotificationBoundary.class))?"granted":"not granted")+
            "\nVoice recognizer: not commissioned\nRaw retention: off",16));
        content.addView(button("Choose assistant",v->{ RoleManager roles=getSystemService(RoleManager.class);
            if(roles.isRoleAvailable(RoleManager.ROLE_ASSISTANT)) startActivityForResult(roles.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT),10); }));
        content.addView(button("Microphone permission",v->requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},11)));
        content.addView(button("Notification access",v->startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))));
        if(Build.VERSION.SDK_INT>=31) content.addView(button("Headset routing permission",v->requestPermissions(new String[]{Manifest.permission.BLUETOOTH_CONNECT},12)));
        if(Build.VERSION.SDK_INT>=33) content.addView(button("Foreground notification permission",v->requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},13)));
        var prefs=getSharedPreferences("permissions",MODE_PRIVATE);
        Switch perception=new Switch(this);perception.setText("Allow selected notification context");perception.setChecked(prefs.getBoolean("notification_context",false));
        Switch replies=new Switch(this);replies.setText("Allow replies after Core approval");replies.setChecked(prefs.getBoolean("notification_reply",false));
        EditText sources=field("Allowed package IDs, separated by commas",false);sources.setText(prefs.getString("notification_sources",""));
        content.addView(perception);content.addView(replies);content.addView(sources);
        new AlertDialog.Builder(this).setTitle("Independent grants").setView(content)
            .setMessage("Perception, retention and action authority are separate. Voice requires a real commissioned binding.")
            .setPositiveButton("Save",(d,w)->prefs.edit().putBoolean("notification_context",perception.isChecked())
                .putBoolean("notification_reply",replies.isChecked()).putString("notification_sources",sources.getText().toString().replace(" ","")).apply())
            .setNegativeButton("Close",null).show();
    }
    private void notifications() {
        try {
            var exposed=NotificationBoundary.exposed();if(exposed.isEmpty()) { response.setText("No permitted notification exposes a reply action.");return; }
            String[] labels=new String[exposed.size()];for(int i=0;i<labels.length;i++) labels[i]=exposed.get(i).getString("title");
            new AlertDialog.Builder(this).setTitle("Reply to an exposed notification").setItems(labels,(d,index)-> {
                JSONObject item=exposed.get(index);EditText reply=field("Your reply",false);
                reply.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(500)});
                new AlertDialog.Builder(this).setTitle(labels[index]).setView(reply).setNegativeButton("Cancel",null)
                    .setPositiveButton("Review with Core",(dialog,which)-> {
                        try { String text=reply.getText().toString();
                            JSONObject proposal=new JSONObject().put("operation","reply").put("package",item.getString("package"))
                                .put("key_hash",item.getString("key_hash")).put("text_hash",NotificationBoundary.hash(text));
                            request("challenge",proposal,challenge->confirm(challenge,value->{
                                NotificationBoundary.send(value.getJSONObject("permit"),text,value.getLong("_request_started_elapsed_ms"));
                                response.setText("Reply handed to the app. Delivery is unverified.");
                            }));
                        } catch(Exception unavailable) { response.setText("Reply unavailable. No send is confirmed."); }
                    }).show();
            }).show();
        } catch(Exception unavailable) { response.setText("Notification access is unavailable."); }
    }
    @Override protected void onResume() { super.onResume();foreground=true;orb.onResume();handler.post(refresh); }
    @Override protected void onPause() {
        foreground=false;generation.incrementAndGet();handler.removeCallbacks(refresh);snapshot=null;tasks.removeAllViews();interactionMessage=null;
        if(confirmation!=null) confirmation.cancel();orb.onPause();super.onPause();
    }
    @Override protected void onDestroy() { network.shutdownNow();orb.destroy();super.onDestroy(); }
}
