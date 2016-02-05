/**
 * @param {string} id - Element ID
 */
function MiningKitLineChart(id, options) {
    this._ctx = document.getElementById(id).getContext('2d');
    this._labels = options.labels;
    this._lineOptions = {
        scaleShowGridLines: true,
        scaleGridLineColor: "rgba(0,0,0,.05)",
        scaleGridLineWidth: 1,
        bezierCurve: true,
        bezierCurveTension: 0.4,
        pointDot: true,
        pointDotRadius: 4,
        pointDotStrokeWidth: 1,
        pointHitDetectionRadius: 20,
        datasetStroke: true,
        datasetStrokeWidth: 2,
        datasetFill: true,
        responsive: true
    };

    var lineData = {
        labels: this._labels,
        datasets: this._generateDatasets(options.lines)
    };

    this._chart = new Chart(this._ctx).Line(lineData, this._lineOptions);
}

/**
 * @param {array} lines - 2d lines array. Example: [[1, 2, 3], [4, 5, 6]]
 */
MiningKitLineChart.prototype.update = function(lines) {
    this._chart.destroy();

    this._lineOptions.animation = false;

    var lineData = {
        labels: this._labels,
        datasets: this._generateDatasets(lines)
    };

    this._chart = new Chart(this._ctx).Line(lineData, this._lineOptions);
};


/**
 * @param {array} lines - 2d lines array. Example: [[1, 2, 3], [4, 5, 6]]
 */
MiningKitLineChart.prototype._generateDatasets = function(lines) {
    var datasets = [];

    var opacity = 0.05;

    lines.forEach(function(line) {
        datasets.push({
            fillColor: "rgba(26,179,148," + opacity + ")",
            strokeColor: "rgba(26,179,148,1)",
            pointColor: "rgba(26,179,148,1)",
            pointStrokeColor: "#fff",
            pointHighlightFill: "#fff",
            pointHighlightStroke: "rgba(26,179,148,1)",
            data: line
        });

        opacity += 0.05;
    });

    return datasets;
};
