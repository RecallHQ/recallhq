

// WebSocket connection setup
let socket = null;



function connectWebSocket() {
    const wsUrl = `wss://${window.location.host}/ws_recall`; // Connect to the same host as the page
    socket = new WebSocket(wsUrl);
    timer_handle = null

    socket.onopen = function(e) {
        console.log("WebSocket connection established");
        socket.send(JSON.stringify("{msg:'HELLO'}"));
        timer_handle = setInterval(sendPing, 3000);    
        
    };

    function sendPing() {
        socket.send("ping");
    };

    socket.onmessage = function(event) {
        console.log("Message from server:", event.data);
        // Handle incoming messages here
        handleIncomingMessage(event.data);
    };

    socket.onclose = function(event) {
        console.log("WebSocket connection closed:", event);
        // Attempt to reconnect after a delay
        setTimeout(connectWebSocket, 5000);
	if (timer_handle != null) {
		clearInterval(timer_handle);
		timer_handle = null;
	}
    };

    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
	if (timer_handle != null) {
		clearInterval(timer_handle);
		timer_handle = null;
	}
    };
}

function sendMessage(message) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    } else {
        console.error("WebSocket is not connected");
    }
}

function handleIncomingMessage(data) {
    console.log("message = ", data)
    try {
        const message = JSON.parse(data);
        
        // Process the message based on its type or content
        switch(message.type) {
            case 'updateVideoInterval':
                handleUpdateVideoInterval(message);
                break;
            case 'setVideoFullscreen':
                handleSetFullscreen(message);
                break;
            case 'unsetVideoFullscreen':
                handleUnsetFullscreen(message);
                break;
            case 'playVideo':
                handlePlayVideo(message);
                break;
            case 'pauseVideo':
                handlePauseVideo(message);
                break;
            case 'fastForward':
                handleFastForwardVideoInterval(message);
                break;
            // Add more cases as needed
            default:
                console.log("Unhandled message type:", message.type);
        }
    } catch (error) {
        console.error("Error parsing incoming message:", error);
    }
}

function handleFastForwardVideoInterval(message) {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        delta_time = message.delta;
        videoElement.currentTime = videoElement.currentTime + delta_time;
        videoElement.play();
    }
}

function handleUpdateVideoInterval(message) {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        start_time = message.start;
        end_time = message.end;
        videoElement.currentTime = start_time;
        videoElement.play();
        videoElement.addEventListener('timeupdate', function () {
            if (videoElement.currentTime >= end_time) {
                videoElement.pause();  // Stop the video at the end time
                videoElement.currentTime = end_time;  // Optionally reset the time to endTime
            }
        });
    }
}

function handleSetFullscreen(message) {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        videoElement.requestFullscreen();
        videoElement.webkitRequestFullscreen()();
    }
}

function handleUnsetFullscreen(message) {
    document.exitFullscreen();
}

function handlePlayVideo(message) {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        videoElement.play();
    }
}

function handlePauseVideo(message) {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        videoElement.pause();
    }
}


// Initialize WebSocket connection
connectWebSocket();
