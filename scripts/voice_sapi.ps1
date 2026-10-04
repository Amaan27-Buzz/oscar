$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$voiceRequest = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName System.Speech
$voiceSynth = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    if ($voiceRequest.voice -ne 'local-system') {
        $voiceSynth.SelectVoice([string]$voiceRequest.voice)
    }
    $voiceSynth.Rate = [int]$voiceRequest.rate
    $voiceFormat = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
        16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono)
    $voiceSynth.SetOutputToWaveFile([string]$voiceRequest.path, $voiceFormat)
    $voiceSynth.Speak([string]$voiceRequest.text)
} finally {
    $voiceSynth.Dispose()
}
