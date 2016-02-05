;(function($) {
    'use strict';

    function fixHeight() {
        var windowHeight = $(window).height();
        $('#page-wrapper').css('min-height', windowHeight + 'px');
    }

    $(document).ready(fixHeight);
    $(window).resize(fixHeight);
}(jQuery));
