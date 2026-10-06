plugins { id("com.android.application") }
android {
    namespace = "io.dawnlight.oscar.sunday"
    compileSdk = 36
    defaultConfig {
        applicationId = "io.dawnlight.oscar.sunday"
        minSdk = 30
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-foundation"
    }
    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    sourceSets["main"].assets.srcDir("../../assets/brand")
}
