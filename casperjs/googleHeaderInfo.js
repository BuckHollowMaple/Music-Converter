var casper = require('casper').create({
    pageSettings: {
        loadImages: true,//The script is much faster when this field is set to false
        loadPlugins: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
    }
});

var term = casper.cli.get('term');

//First step is to open NS
casper.start().thenOpen("https://www.google.com/search?q=" + term, function() {
});

casper.then(function(){
    var general = this.evaluate(function(){
        return document.querySelector("div._PWc h3 a").textContent;
    });

    return require('utils').dump(general);
});


casper.run();
