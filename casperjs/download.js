var casper = require('casper').create({
    waitTimeout: 30000,
    stepTimeout: 30000,
    pageSettings: {
        loadImages: false,
        loadPlugins: true,
        userAgent: '"Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0"'
    }
});

var term = casper.cli.get('term');

casper.start().thenOpen("http://musicpleer.audio/", function() {
});

casper.then(function(){
    casper.sendKeys('#searchField',term); 
});

casper.wait(1000, function(){
    this.evaluate(function(){
	    document.getElementsByClassName('ui-btn ui-btn-icon-right ui-icon-arrow-r')[0].click();
    });
});

casper.wait(1000, function(){
    var num = casper.cli.get('attempt');
    this.evaluate(function(n){
	    document.getElementsByClassName('ui-btn')[n].click();
    }, num);
});

casper.wait(1000, function(){
    var url_get = this.evaluate(function(){
        return document.getElementById("download-btn").href;
    });

    console.log(require('utils').dump(url_get));
});

casper.run();
