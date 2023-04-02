const recordButton = document.getElementById("recordButton");
let isRecording = false;
let mediaRecorder;

recordButton.addEventListener("click", () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    isRecording = true;
    recordButton.innerText = "Stop";
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.start();

    const audioChunks = [];
    mediaRecorder.addEventListener("dataavailable", (event) => {
        audioChunks.push(event.data);
    });

    mediaRecorder.addEventListener("stop", () => {
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        sendAudioToServer(audioBlob);
    });
}

function stopRecording() {
    isRecording = false;
    recordButton.innerText = "Record";
    mediaRecorder.stop();
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recorded_audio.webm");

    fetch("/upload_audio", {
        method: "POST",
        body: formData,
    }).then((response) => {
        if (response.ok) {
            console.log("Audio uploaded successfully.");
        } else {
            console.error("Failed to upload audio.");
        }
    });
}