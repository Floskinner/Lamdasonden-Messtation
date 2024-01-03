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
    console.log("Error connecting to server: " + error);
});

socket.on("disconnect", (reason) => {
    console.log("Disconnected from server: " + reason);
    if (reason === "io server disconnect") {
        // the disconnection was initiated by the server, you need to reconnect manually
        socket.connect();
    }
    // else the socket will automatically try to reconnect
});

socket.on("connect_error", (error) => {
    console.log("Error connecting to server: " + error);
});

socket.on("disconnect", (reason) => {
    console.log("Disconnected from server: " + reason);
    if (reason === "io server disconnect") {
        // the disconnection was initiated by the server, you need to reconnect manually
        socket.connect();
    }
    // else the socket will automatically try to reconnect
});

socket.on('disconnect', function () {
    socket.emit('disconnect', {
        data: 'User Disconnected'
    });
});



socket.on('newValues', function (values) {
    // console.log(JSON.stringify(values));

    const lamda1 = values.lamda1;
    const lamda2 = values.lamda2;
    const afr1 = values.afr1;
    const afr2 = values.afr2;
    const temp1 = values.temp1;
    const temp2 = values.temp2;

    updateValuesOnScreen(lamda1, lamda2, afr1, afr2, temp1, temp2);

    applyWarningColorsLambda($("#lamda1"), lamda1);
    applyWarningColorsLambda($("#lamda2"), lamda2);

    applyWarningColorsTemp($("#temp1"), temp1);
    applyWarningColorsTemp($("#temp2"), temp2);

    if ((lamda1 >= MAX_LAMBDA_ABOVE_RED || lamda1 <= MAX_LAMBDA_BELOW_RED) && blinking) {
        applyRedBlinking($("#lamda1"));
    }
    if ((lamda2 >= MAX_LAMBDA_ABOVE_RED || lamda2 <= MAX_LAMBDA_BELOW_RED) && blinking) {
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