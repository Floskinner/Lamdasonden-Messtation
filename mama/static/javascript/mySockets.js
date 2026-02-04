const socket = io.connect('http://' + document.domain + ':' + location.port);

const RED = "rgb(179, 0, 0)";
const ORANGE = "rgb(227, 111, 39)";
const BLACK = "rgb(0, 0, 0)";

const MAX_LAMBDA_ABOVE_ORANGE = 1.12;
const MAX_LAMBDA_ABOVE_RED = 1.20;

const MAX_LAMBDA_BELOW_ORANGE = 0.86;
const MAX_LAMBDA_BELOW_RED = 0.80;

const MAX_TEMP_ABOVE_ORANGE = 600;
const MAX_TEMP_ABOVE_RED = 850;

const MAX_SHOWN_LAMBDA_LIMIT = 1.500
const MIN_SHOWN_LAMBDA_LIMIT = 0.550

const MAX_SHOWN_AFR_LIMIT = 21.0
const MIN_SHOWN_AFR_LIMIT = 8.09

let hinweis_queue = [];

let blinking = undefined;
let decimalPlaces = undefined;

socket.on('connect', function () {
    let browserTime = new Date().toISOString();

    socket.emit('connected', {
        data: browserTime
    });
});

socket.on("connect_error", (error) => {
    // Connection error handling - reconnection is automatic
});

socket.on("disconnect", (reason) => {
    if (reason === "io server disconnect") {
        // the disconnection was initiated by the server, you need to reconnect manually
        socket.connect();
    }
    // else the socket will automatically try to reconnect
});



socket.on('newValues', function (values) {
    console.log(JSON.stringify(values));

    const lamda1 = Math.max(Math.min(values.lamda1, MAX_SHOWN_LAMBDA_LIMIT), MIN_SHOWN_LAMBDA_LIMIT);
    const lamda2 = Math.max(Math.min(values.lamda2, MAX_SHOWN_LAMBDA_LIMIT), MIN_SHOWN_LAMBDA_LIMIT);
    const afr1 = Math.max(Math.min(values.afr1, MAX_SHOWN_AFR_LIMIT), MIN_SHOWN_AFR_LIMIT);
    const afr2 = Math.max(Math.min(values.afr2, MAX_SHOWN_AFR_LIMIT), MIN_SHOWN_AFR_LIMIT);
    const temp1 = values.temp1;
    const temp2 = values.temp2;

    updateValuesOnScreen(lamda1, lamda2, afr1, afr2, temp1, temp2);

    applyWarningColorsLambda($("#lamda1"), lamda1);
    applyWarningColorsLambda($("#lamda2"), lamda2);

    applyWarningColorsTemp($("#temp1"), temp1);
    applyWarningColorsTemp($("#temp2"), temp2);

    if ((lamda1 >= MAX_LAMBDA_ABOVE_RED || lamda1 <= MAX_LAMBDA_BELOW_RED) && blinking && !(lamda1 >= MAX_SHOWN_LAMBDA_LIMIT || lamda1 <= MIN_SHOWN_LAMBDA_LIMIT)) {
        applyRedBlinking($("#lamda1"));
    }
    if ((lamda2 >= MAX_LAMBDA_ABOVE_RED || lamda2 <= MAX_LAMBDA_BELOW_RED) && blinking && !(lamda2 >= MAX_SHOWN_LAMBDA_LIMIT || lamda2 <= MIN_SHOWN_LAMBDA_LIMIT)) {
        applyRedBlinking($("#lamda2"));
    }
});


socket.on("error", (error) => {
    console.log(error);

    if (error.type === "config") {
        $("#errorModalInfoText").html("Es scheint, als ob die Konfiguration nicht korrekt ist. Bitte überprüfe die Konfiguration (settings.json) und starte die MAMA neu.");
        $("#errorModalInfoTextDiv").show();
    }
    else {
        $("#errorModalInfoTextDiv").hide();
    }

    $("#errorModalShort").html(error.exc);
    $("#errorModalTraceback").html(error.traceback);

    $('#errorModal').css('display', 'block');
});

socket.on("info", (info) => {
    console.log(info);
    hinweis_queue.push(info.msg);

    showAllInfos();

    // Clear the queue after 5 seconds
    setTimeout(function () {
        hinweis_queue = [];
    } , 5000);
});

function showAllInfos() {
    $("#infoModalInfoText").html(hinweis_queue.join("<br>"));
    $('#infoModal').css('display', 'block');
}

function updateValuesOnScreen(lamda1, lamda2, afr1, afr2, temp1, temp2) {
    $('#lamda1').html(lamda1.toFixed(decimalPlaces) + " &lambda;");
    $('#lamda2').html(lamda2.toFixed(decimalPlaces) + " &lambda;");
    $('#afr1').html(afr1.toFixed(2) + " AFR");
    $('#afr2').html(afr2.toFixed(2) + " AFR");

    $('#temp1').html(temp1 + " &#8451");
    $('#temp2').html(temp2 + " &#8451");
}

function applyWarningColorsLambda(htmlElement, lambdaValue) {
    // Sind die Werte von Lamda entsprechend, wird der Text erst Orange und dann Rot
    if (lambdaValue >= MAX_LAMBDA_ABOVE_ORANGE || lambdaValue <= MAX_LAMBDA_BELOW_ORANGE) {
        if (lambdaValue >= MAX_LAMBDA_ABOVE_RED || lambdaValue <= MAX_LAMBDA_BELOW_RED) {
            htmlElement.css("color", RED);
        } else {
            htmlElement.css("color", ORANGE);
        }
    } else {
        htmlElement.css("color", BLACK);
    }
}

function applyWarningColorsTemp(htmlElement, tempValue) {
    if (tempValue >= MAX_TEMP_ABOVE_ORANGE) {
        if (tempValue >= MAX_TEMP_ABOVE_RED) {
            htmlElement.css("color", RED);
        } else {
            htmlElement.css("color", ORANGE);
        }
    } else {
        htmlElement.css("color", BLACK);
    }
}

async function applyRedBlinking(htmlElement) {
    await Sleep(UPDATE_INTERVALL / 2);
    htmlElement.css("color", "rgba(0,0,0,0)");
}

function Sleep(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}
