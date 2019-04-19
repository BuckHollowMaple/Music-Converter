var casper = require('casper').create({
    waitTimeout: 30000,
    stepTimeout: 30000,
    pageSettings: {
        loadImages: false,
        loadPlugins: true,
        userAgent: '"Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0"'
    }
});

var url = casper.cli.get('url');

casper.start().thenOpen("https://www.youtube.com/signin", function() {
});

casper.then(function(){
    this.evaluate(function(){
	    document.getElementById('identifierId').value = 'harrisonking1883@gmail.com';
	    document.getElementById('identifierNext').click();
    });
});

casper.wait(2000, function(){
    this.evaluate(function(){
	    document.getElementsByTagName('input')[2].value = 'Howe&ser1883';
	    document.getElementsByTagName('input')[2].setAttribute('badinput', 'false');
	    document.getElementsByTagName('form')[0].submit();
	    document.getElementById('passwordNext').click();
    });
    this.capture('google.png');    
});


casper.thenOpen("https://www.youtube.com/edit?o=U&video_id=" + url, function() {
    this.evaluate(function(){
	    document.getElementsByClassName('tab-header-title')[2].click();
	    document.getElementById('monetize-with-ads').check();
	    document.getElementById('monetize-with-ads').checked = true;
    });


});

casper.run();
