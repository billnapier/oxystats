google.load('visualization', '1', {packages: ['annotatedtimeline', 'columnchart', 'table']});
function drawVisualization() {
    var url = '/data_';
{% ifequal when 'alltime' %}
    var q = new google.visualization.Query(url + "by_day");
    q.send(function(response) {
               new google.visualization.AnnotatedTimeLine(document.getElementById('timeline')).
                   draw(response.getDataTable(), {title: 'Messages by Day'});
           });
    var q2 = new google.visualization.Query(url + "by_hour")
        q2.send(function(response) {
                    var dt = response.getDataTable();
                    // Jump through the hoops to get the hour returned as a string so the graph looks right
                    var dv = new google.visualization.DataView(dt);
                    dv.setColumns([0, 2]);
                    new google.visualization.ColumnChart(document.getElementById('hours')).
                        draw(dv, {is3D: true, title: 'Messages by Hour'});

                });
{% endifequal %}
    var q3 = new google.visualization.Query(url + "by_author?limit={{limit}}&when={{when}}");
    q3.send(function(response) {
                var table1 = new google.visualization.Table(document.getElementById('byperson'));
                table1.draw(response.getDataTable(), {
                    title: 'Messages by Person',
                                   sort: 'enable'}
                    );
            });
    var q4 = new google.visualization.Query(url + "by_subject?limit={{limit}}&when={{when}}");
    q4.send(function(response) {
                new google.visualization.Table(document.getElementById('bysubject')).
                    draw(response.getDataTable(), {title: 'Messages by Subject'});
            });
    var q6 = new google.visualization.Query(url + "by_tag?limit={{limit}}&when={{when}}");
    q6.send(function(response) {
                new google.visualization.Table(document.getElementById('bytag')).
                    draw(response.getDataTable(), {title: 'Messages by Tag'});
            });
}

google.setOnLoadCallback(drawVisualization);
