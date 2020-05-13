let getDeathData = function (state) {
    $.when(
        $.ajax({
            url: "_deaths",
            datatype: 'json',
            data: {state: state, date: store.today},
            success: function (data) {
                store.data2 = data;
            }
        }),
        $.ajax({
            url: '_lmfit_deaths',
            datatype: 'json',
            data: {state: state, date: store.today},
            success: function (data) {
                store.fit2 = data;
            }
        })
    ).then(function () {
        deathDraw(store.data2, store.fit2)
    })
};

let deathDraw = function (data, fit) {
    let x = Object.keys(data).map(function (item) {
        return parseInt(item)
    });
    let y = Object.values(data);
    let x0 = Object.keys(fit).map(function (item) {
        return parseInt(item)
    });
    let y0 = Object.values(fit);
    let currentDay = x[x.length - 1];
    updateDeathText(y, y0, x0.indexOf(currentDay));
    currentDeaths(x, y, x0, y0, currentDay);
    predDeaths(x, y, x0, y0);
    deathRate()
};

let updateDeathText = function (y, y0, currentDay) {
    let yCases = Object.values(store.data);
    let y0Cases = Object.values(store.fit);
    let dr = y[y.length - 1] / yCases[yCases.length - 1];
    $("#current-deaths-txt").find('h3').text(y[y.length - 1].toLocaleString());
    $("#death-rate-txt").find('h3').text((100 * dr).toLocaleString() + '%');
    $("#pred-deaths-txt").find('h3').text(y0[y0.length - 1].toLocaleString());
    $("#pred-deaths-dr-txt").find('h3').text(Math.round((y0Cases[y0Cases.length - 1] * dr)).toLocaleString());
    $('#tom-new-deaths-txt').find('h3').text((y0[currentDay + 1] - y0[currentDay]).toLocaleString());
    $('#new-deaths-txt h3').text((y[y.length - 1] - y[y.length - 2]).toLocaleString());
};


let currentDeaths = function (x, y, x0, y0, currentDay) {
    let trace1 = {
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter',
        name: 'Data'
    };
    let index = x0.indexOf(currentDay);
    let trace2 = {
        x: x0.slice(0, index + 1),
        y: y0.slice(0, index + 1),
        mode: 'lines',
        type: 'scatter',
        name: 'Fit'
    };
    let layout = {
        title: {text: 'Total Deaths', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'Total Deaths'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('current-deaths', [trace1, trace2], layout, config);
};

let predDeaths = function (x, y, x0, y0) {
    let trace1 = {
        x: x,
        y: y,
        type: 'scatter',
        mode: 'markers',
        name: 'Data'
    };
    let trace2 = {
        x: x0,
        y: y0,
        mode: 'lines',
        type: 'scatter',
        name: 'Prediction'
    };
    let layout = {
        title: {text: 'Total Predicted Deaths', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'Total Deaths'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('pred-deaths', [trace1, trace2], layout, config);
};


let deathRate = function () {
    let result = Object.keys(store.data2).map(function (key, index) {
        return 100 * store.data2[key] / store.data[key];
    });

    let trace1 = {
        x: Object.keys(store.data2),
        y: result,
        mode: 'lines+markers',
        type: 'scatter'
    };
    let layout = {
        title: {text: "Death Rate", y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'Death Rate (%)'},
        font: {family: "Courier New, monospace", size: 18},
        showlegend: false
    };
    let config = {responsive: true};
    Plotly.newPlot('death-rate', [trace1], layout, config);
};