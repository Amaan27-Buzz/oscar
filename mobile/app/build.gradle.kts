plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}
android {
    namespace = "io.dawnlight.oscar.mobile"
    compileSdk = 36
    defaultConfig {
        applicationId = "io.dawnlight.oscar.mobile"
        minSdk = 30
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-foundation"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    buildFeatures { buildConfig = true; compose = true }
    buildTypes {
        create("review") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".review"
            matchingFallbacks += "debug"
        }
    }
    testBuildType = providers.gradleProperty("oscarTestBuildType").getOrElse("debug")
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    sourceSets["main"].assets.srcDir("../../assets/brand")
    sourceSets["review"].res.srcDir("src/debug/res")
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
dependencies {
    implementation(project(":expression"))
    implementation(platform("androidx.compose:compose-bom:2026.03.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.activity:activity-compose:1.12.4")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.10.0")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.10.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("org.commonmark:commonmark:0.30.1")
    implementation("org.commonmark:commonmark-ext-gfm-tables:0.30.1")
    implementation("org.commonmark:commonmark-ext-gfm-strikethrough:0.30.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20251224")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
    androidTestImplementation(platform("androidx.compose:compose-bom:2026.03.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test:runner:1.7.0")
    // Android 16 removed the reflective InputManager entry point used by older Espresso.
    androidTestImplementation("androidx.test.espresso:espresso-core:3.7.0")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
    add("reviewImplementation", "androidx.compose.ui:ui-test-manifest")
}
