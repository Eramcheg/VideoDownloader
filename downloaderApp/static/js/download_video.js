function downloadVideoWithAudio(format,downloadUrl) {
    const url = document.getElementById("url").value;
    const csrf_token = getCookie('csrftoken');
    showOverlay();
    fetch(downloadUrl, {//"{% url 'download_video_with_format' %}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        },
        body: JSON.stringify({
            'url': url,
            'format_id': selectedAudioFormat,
        })
    })
    .then(response => {
        if (response.ok) {
            closeModal();
            return response.blob();
        } else {
            throw new Error("Failed to download video with audio");
        }
    })
    .then(blob => {
        const downloadLink = document.createElement("a");
        downloadLink.href = window.URL.createObjectURL(blob);
        downloadLink.download = "video_with_audio.mp4";
        downloadLink.click();
    })
    .catch(error => console.error("Error:", error))
    .finally(() => hideOverlay());
}