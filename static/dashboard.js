// ============================================================
// Industrial Monitoring System
// Complete Dashboard JavaScript
// ============================================================


// ============================================================
// LIVE CHART DATA
// ============================================================

const vibrationLabels = [];

const xData = [];
const yData = [];
const zData = [];

const electricalLabels = [];

const voltageData = [];
const currentData = [];
const powerData = [];

const MAX_POINTS = 30;


// ============================================================
// LIVE VIBRATION CHART
// ============================================================

const vibrationChart = new Chart(
    document.getElementById("vibrationChart"),
    {
        type: "line",

        data: {
            labels: vibrationLabels,

            datasets: [

                {
                    label: "X Axis",
                    data: xData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                },

                {
                    label: "Y Axis",
                    data: yData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                },

                {
                    label: "Z Axis",
                    data: zData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                }

            ]
        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            animation: false,

            scales: {

                x: {
                    title: {
                        display: true,
                        text: "Time"
                    }
                },

                y: {
                    title: {
                        display: true,
                        text: "Acceleration (m/s²)"
                    }
                }

            }
        }
    }
);


// ============================================================
// LIVE ELECTRICAL CHART
// ============================================================

const electricalChart = new Chart(
    document.getElementById("electricalChart"),
    {
        type: "line",

        data: {
            labels: electricalLabels,

            datasets: [

                {
                    label: "Voltage (V)",
                    data: voltageData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                },

                {
                    label: "Current (mA)",
                    data: currentData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                },

                {
                    label: "Power (W)",
                    data: powerData,
                    borderWidth: 2,
                    tension: 0.2,
                    pointRadius: 0
                }

            ]
        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            animation: false,

            scales: {

                x: {
                    title: {
                        display: true,
                        text: "Time"
                    }
                },

                y: {
                    title: {
                        display: true,
                        text: "Electrical Value"
                    }
                }

            }
        }
    }
);


// ============================================================
// UPDATE MACHINE CONDITION
// ============================================================

function updateCondition(condition) {

    const element =
        document.getElementById("condition");

    element.textContent = condition;

    element.classList.remove(
        "normal",
        "warning",
        "danger"
    );

    if (condition === "NORMAL") {

        element.classList.add("normal");

    }

    else if (condition === "WARNING") {

        element.classList.add("warning");

    }

    else if (condition === "DANGER") {

        element.classList.add("danger");

    }
}


// ============================================================
// UPDATE DASHBOARD VALUES
// ============================================================

function updateDashboard(data) {

    // --------------------------------------------------------
    // Vibration values
    // --------------------------------------------------------
    document.getElementById("energy").textContent =
        Number(data.energy_Wh).toFixed(4);

    document.getElementById("rms").textContent =
        Number(data.rms).toFixed(4);

    document.getElementById("peak").textContent =
        Number(data.peak).toFixed(4);

    document.getElementById("frequency").textContent =
        Number(data.frequency).toFixed(2);


    // --------------------------------------------------------
    // Electrical values
    // --------------------------------------------------------

    document.getElementById("voltage").textContent =
        Number(data.voltage).toFixed(2);

    document.getElementById("current").textContent =
        Number(data.current).toFixed(2);

    document.getElementById("power").textContent =
        Number(data.power).toFixed(3);


    // --------------------------------------------------------
    // Timestamp
    // --------------------------------------------------------

    document.getElementById("timestamp").textContent =
        data.time;


    // --------------------------------------------------------
    // Machine condition
    // --------------------------------------------------------

    updateCondition(data.condition);


    // ========================================================
    // UPDATE LIVE VIBRATION GRAPH
    // ========================================================

    vibrationLabels.push(data.time);

    xData.push(data.x);
    yData.push(data.y);
    zData.push(data.z);


    if (vibrationLabels.length > MAX_POINTS) {

        vibrationLabels.shift();

        xData.shift();
        yData.shift();
        zData.shift();

    }


    vibrationChart.update();


    // ========================================================
    // UPDATE LIVE ELECTRICAL GRAPH
    // ========================================================

    electricalLabels.push(data.time);

    voltageData.push(data.voltage);
    currentData.push(data.current);
    powerData.push(data.power);


    if (electricalLabels.length > MAX_POINTS) {

        electricalLabels.shift();

        voltageData.shift();
        currentData.shift();
        powerData.shift();

    }


    electricalChart.update();

}


// ============================================================
// GET MACHINE DATA FROM FLASK
// ============================================================

async function getMachineData() {

    try {

        const response =
            await fetch("/api/data");

        if (!response.ok) {

            throw new Error(
                "Server returned " + response.status
            );

        }

        const data =
            await response.json();

        updateDashboard(data);

        document.getElementById(
            "serverStatus"
        ).textContent = "● SERVER ONLINE";

    }

    catch (error) {

        console.error(
            "Could not retrieve machine data:",
            error
        );

        document.getElementById(
            "serverStatus"
        ).textContent = "● SERVER OFFLINE";

    }

}


// ============================================================
// GET SYSTEM STATUS
// ============================================================

async function getSystemStatus() {

    try {

        const response =
            await fetch("/api/status");

        const status =
            await response.json();


        document.getElementById(
            "esp32Status"
        ).textContent = status.esp32;


        document.getElementById(
            "wifiStatus"
        ).textContent = status.wifi;


        document.getElementById(
            "rtcStatus"
        ).textContent = status.rtc;


        document.getElementById(
            "sdStatus"
        ).textContent = status.sd;

    }

    catch (error) {

        console.error(
            "Could not retrieve system status:",
            error
        );

    }

}


// ============================================================
// HISTORICAL CHARTS
// ============================================================

let historicalChart = null;

let electricalHistoryChart = null;


async function loadHistoricalData() {

    try {

        const response =
            await fetch("/api/history");


        if (!response.ok) {

            throw new Error(
                "History API returned " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "Historical data:",
            data
        );


        // ====================================================
        // HISTORICAL DATA ARRAYS
        // ====================================================

        const labels = data.map(
            row => row.time
        );


        const rmsValues = data.map(
            row => Number(row.rms)
        );


        const peakValues = data.map(
            row => Number(row.peak)
        );


        const voltageValues = data.map(
            row => Number(row.voltage)
        );


        const currentValues = data.map(
            row => Number(row.current)
        );


        const powerValues = data.map(
            row => Number(row.power)
        );


        // ====================================================
        // HISTORICAL VIBRATION CHART
        // ====================================================

        const historicalCanvas =
            document.getElementById(
                "historicalChart"
            );


        if (historicalCanvas) {

            if (historicalChart) {

                historicalChart.destroy();

            }


            historicalChart = new Chart(

                historicalCanvas.getContext("2d"),

                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label: "RMS",
                                data: rmsValues,
                                borderWidth: 2,
                                tension: 0.2,
                                pointRadius: 0
                            },

                            {
                                label: "Peak",
                                data: peakValues,
                                borderWidth: 2,
                                tension: 0.2,
                                pointRadius: 0
                            }

                        ]

                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        scales: {

                            x: {

                                title: {

                                    display: true,

                                    text: "Time"

                                }

                            },


                            y: {

                                beginAtZero: true,

                                title: {

                                    display: true,

                                    text: "Vibration"

                                }

                            }

                        }

                    }

                }

            );

        }


        // ====================================================
        // HISTORICAL ELECTRICAL CHART
        // ====================================================

        const electricalHistoryCanvas =
            document.getElementById(
                "electricalHistoryChart"
            );


        if (electricalHistoryCanvas) {

            if (electricalHistoryChart) {

                electricalHistoryChart.destroy();

            }


            electricalHistoryChart = new Chart(

                electricalHistoryCanvas.getContext("2d"),

                {

                    type: "line",

                    data: {

                        labels: labels,

                        datasets: [

                            {
                                label: "Voltage (V)",
                                data: voltageValues,
                                borderWidth: 2,
                                tension: 0.2,
                                pointRadius: 0
                            },

                            {
                                label: "Current (mA)",
                                data: currentValues,
                                borderWidth: 2,
                                tension: 0.2,
                                pointRadius: 0
                            },

                            {
                                label: "Power (W)",
                                data: powerValues,
                                borderWidth: 2,
                                tension: 0.2,
                                pointRadius: 0
                            }

                        ]

                    },


                    options: {

                        responsive: true,

                        maintainAspectRatio: false,

                        scales: {

                            x: {

                                title: {

                                    display: true,

                                    text: "Time"

                                }

                            },


                            y: {

                                beginAtZero: true,

                                title: {

                                    display: true,

                                    text: "Electrical Value"

                                }

                            }

                        }

                    }

                }

            );

        }

    }


    catch (error) {

        console.error(
            "Historical data error:",
            error
        );

    }

}
// ============================================================
// MACHINE EVENT LOG
// ============================================================

async function getMachineEvents() {

    try {

        const response =
            await fetch("/api/events");

        if (!response.ok) {
            throw new Error(
                "Events API returned " +
                response.status
            );
        }

        const events =
            await response.json();

        const eventLog =
            document.getElementById("eventLog");

        if (!eventLog) {
            return;
        }

        if (events.length === 0) {

            eventLog.innerHTML = `
                <div class="event-item">
                    <span>--:--:--</span>
                    <strong>SYSTEM</strong>
                    <p>
                        No machine events yet.
                    </p>
                </div>
            `;

            return;
        }

        eventLog.innerHTML = "";

        events
            .slice()
            .reverse()
            .forEach(event => {

                const eventItem =
                    document.createElement("div");

                eventItem.className =
                    "event-item " +
                    event.condition.toLowerCase();

                eventItem.innerHTML = `
                    <span>${event.time}</span>
                    <strong>${event.condition}</strong>
                    <p>${event.message}</p>
                `;

                eventLog.appendChild(
                    eventItem
                );

            });

    } catch (error) {

        console.error(
            "Event log error:",
            error
        );

    }
}

// ============================================================
// START DASHBOARD
// ============================================================

getMachineData();

getSystemStatus();

loadHistoricalData();


// ============================================================
// UPDATE MACHINE DATA EVERY SECOND
// ============================================================

setInterval(
    getMachineData,
    1000
);


// ============================================================
// UPDATE SYSTEM STATUS EVERY 5 SECONDS
// ============================================================

setInterval(
    getSystemStatus,
    5000
);


// ============================================================
// REFRESH HISTORICAL DATA EVERY 10 SECONDS
// ============================================================

setInterval(
    loadHistoricalData,
    10000
);
setInterval(
    getMachineEvents,
    2000
);

getMachineEvents();
