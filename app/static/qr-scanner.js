const
    el = {},
    usingOffscreenCanvas = isOffscreenCanvasWorking();

document
    .querySelectorAll('[id]')
    .forEach(element => el[element.id] = element)

let
    offCanvas,
    afterPreviousCallFinished,
    requestId = null;

// el.usingOffscreenCanvas.innerText = usingOffscreenCanvas ? 'yes' : 'no'


function isOffscreenCanvasWorking() {
    try {
        return Boolean((new OffscreenCanvas(1, 1)).getContext('2d'))

    } catch {
        return false
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function stopScanner() {
    document.getElementById("video").srcObject = null;
    // Don't reload immediately - let the connection processing modal handle it
}

function detect(source) {
    const
        canvas = document.getElementById("canvas"),
        ctx = canvas.getContext('2d');

    function getOffCtx2d(width, height) {
        if (usingOffscreenCanvas) {
            if (!offCanvas || (offCanvas.width !== width) || (offCanvas.height !== height)) {
                // Only resizing the canvas caused Chromium to become progressively slower
                offCanvas = new OffscreenCanvas(width, height)
            }

            return offCanvas.getContext('2d')
        }
    }

    canvas.width = source.naturalWidth || source.videoWidth || source.width
    canvas.height = source.naturalHeight || source.videoHeight || source.height

    if (canvas.height && canvas.width) {
        const offCtx = getOffCtx2d(canvas.width, canvas.height) || ctx

        offCtx.drawImage(source, 0, 0)

        const
            imageData = offCtx.getImageData(0, 0, canvas.width, canvas.height);

        return zbarWasm
            .scanImageData(imageData)
            .then(symbols => {
                symbols.forEach(symbol => {
                    const lastPoint = symbol.points[symbol.points.length - 1]
                    ctx.moveTo(lastPoint.x, lastPoint.y)
                    symbol.points.forEach(point => ctx.lineTo(point.x, point.y))

                    ctx.lineWidth = Math.max(Math.min(canvas.height, canvas.width) / 100, 1)
                    ctx.strokeStyle = '#00e00060'
                    ctx.stroke()
                })

                symbols.forEach(s => s.rawValue = s.decode("utf-8"))
                const result = JSON.parse(JSON.stringify(symbols, null, 2))
                if (typeof result[0] !== 'undefined') {
                    document.getElementById("video").srcObject = null;
                    $('#qr-loader').removeAttr("hidden");
                    $('#qr-reader').removeAttr("hidden");
                    $.post("/scanner",
                        {
                            payload: result[0].rawValue,
                        },
                        () => {
                            // Close scanner modal
                            stopScanner();
                            const scannerModal = bootstrap.Modal.getInstance(document.getElementById('scanner-modal'));
                            if (scannerModal) {
                                scannerModal.hide();
                            }
                            // BUG #21: connectionless present-proof request inside OOB (redirect form)
                            if (data && data.result && data.result.action === "presentation_request") {
                                if (data.result.exchange_id) {
                                    window.location.href = `/presentations/${data.result.exchange_id}`;
                                } else {
                                    // fallback: reload so notification / inbox shows
                                    window.location.reload();
                                }
                                return;
                            }
                            
                            // Show connection processing modal with auto-refresh
                            showConnectionProcessing();
                        });
                }
            })

    } else {
        el.result.innerText = 'Source not ready'
        el.timing.className = ''

        return Promise.resolve()
    }
}

function detectVideo(active) {
    if (active) {
        detect(document.getElementById("video"))
            .then(() => requestId = requestAnimationFrame(() => detectVideo(true)))

    } else {
        cancelAnimationFrame(requestId)
        requestId = null
    }
}

el.videoBtn.addEventListener('click', event => {
    if (!requestId) {
        navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: 'environment' } })
            .then(stream => {
                document.getElementById("video").srcObject = stream
                detectVideo(true)
            })
            .catch(error => {
                console.log(error)
            })

    } else {
        el.videoBtn.className = ''
        detectVideo(false)
    }
})
