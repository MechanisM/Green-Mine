/* Backlog Stats */

var StatsModel = Backbone.Model.extend({
    url: function() {
        return this.get('view').$el.attr('url');
    }
});

var StatsView = Backbone.View.extend({
    el: $(".user-story-stats"),

    initialize: function() {
        _.bindAll(this, 'render', 'reload');
        this.model = new StatsModel({view:this});
        this.model.fetch({success:this.render});
    },

    reload: function() {
        this.model.fetch({success:this.render});
    },

    render: function() {
        this.$el.html(this.model.get('stats_html'));
    }
});

/* Burndown */
var BurndownModel = Backbone.Model.extend({
    url: function() {
        return this.get('view').$el.attr('url');
    }
});

var BurndownView = Backbone.View.extend({
    el: $("#burndown"),

    initialize: function() {
        _.bindAll(this, 'render', 'reload');
        if (this.$el.attr('show') === 'on') {
            this.model = new BurndownModel({'view':this});
            this.model.fetch({success:this.render});
        }
    },

    reload: function() {
        if (this.$el.attr('show') === 'on') {
            this.model.fetch({success:this.render});
        }
    },

    render: function() {
        if (this.$el.attr('show') !== 'on') {
            return;
        }

        this.$("#burndown-graph").show();

        var d1 = new Array(),
            d2 = new Array(),
            d3 = new Array(),
            d4 = new Array(),
            ticks = new Array();

        var total_points = this.model.get('total_points');
        var points_for_sprint = this.model.get('points_for_sprint');
        var sprints = this.model.get('sprints_number');
        var extra_points = this.model.get('extra_points');
        var now_position = this.model.get('now_position');

        ticks.push([1,"Kickoff"]);
        for(var i=0; i<=sprints; i++) {
            if(now_position && (points_for_sprint[i+1]==null)) {
                d1.push([now_position, total_points - points_for_sprint[i]]);
            } else {
                d1.push([i+1, total_points - points_for_sprint[i]]);
            }
            d2.push([i+1, total_points - ((total_points/sprints)*i)]);
            if(now_position && (extra_points[i+1]==null)) {
                d3.push([now_position, -extra_points[i]]);
            } else {
                d3.push([i+1, -extra_points[i]]);
            }
            ticks.push([i+2,"Sprint "+(i+1)])
        }

        var min_extra_points = _.reduce(d3, function(memo, num){
            if(num[1]) {
                return Math.min(memo, num[1]);
            } else {
                return memo;
            }
        }, 0);

        $.plot(this.$('#burndown-graph'), [
            {
                data: d2,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#eec446'
            },
            {
                data: d1,
                lines: { show: true, fill: false },
                points: { show: true },
                color: '#669900'
            },
            {
                data: d3,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#cb4b4b'
            },
            {
                data: [[now_position, min_extra_points-5], [now_position, total_points+5]],
                lines: { show: true, fill: true },
                points: { show: false },
                color: "#888888",
            }
        ],
        {
            xaxis: { ticks: ticks },
            yaxis: { position: "right", labelWidth: 40 },
            grid: { borderWidth: 0 }
        });
    }
});

/* Burnup */

var BurnupModel = Backbone.Model.extend({
    url: function() {
        return this.get('view').$el.attr('url');
    }
});

var BurnupView = Backbone.View.extend({
    el: $("#burnup"),

    initialize: function() {
        _.bindAll(this, 'render', 'reload');
        if (this.$el.attr('show') === 'on') {
            this.model = new BurnupModel({'view':this});
            this.model.fetch({success:this.render});
        }
    },

    reload: function() {
        if (this.$el.attr('show') === 'on') {
            this.model.fetch({success:this.render});
        }
    },

    render: function() {
        if (this.$el.attr('show') !== 'on') {
            return;
        }

        this.$("#burnup-graph").show();

        var d1 = new Array(),
            d2 = new Array(),
            d3 = new Array(),
            d4 = new Array(),
            ticks = new Array();

        var sprints = this.model.get('sprints');
        var total_points = this.model.get('total_points');
        var total_sprints = this.model.get('total_sprints');
        var now_position = this.model.get('now_position');

        ticks.push([1,"Kickoff"]);
        for(var i=0; i<=total_sprints; i++) {
            d1.push([i+1, total_points]);

            if(now_position && (sprints[0][i+1]==null)) {
                d2.push([now_position, sprints[0][i]]);
            } else {
                d2.push([i+1, sprints[0][i]]);
            }

            if(now_position && (sprints[1][i+1]==null)) {
                d3.push([now_position, sprints[1][i]]);
            } else {
                d3.push([i+1, sprints[1][i]]);
            }

            if(now_position && (sprints[2][i+1]==null)) {
                d4.push([now_position, sprints[2][i]]);
            } else {
                d4.push([i+1, sprints[2][i]]);
            }
            ticks.push([i+2,"Sprint "+(i+1)]);
        }
        console.log(ticks);
        var max_extra_points = _.reduce(d4, function(memo, num){
            if(num[1] != undefined) {
                return Math.max(memo, num[1]);
            } else {
                return memo;
            }
        }, 0);
        max_extra_points += _.reduce(d3, function(memo, num){
            if(num[1] != undefined) {
                return Math.max(memo, num[1]);
            } else {
                return memo;
            }
        }, 0);

        $.plot($("#burnup-graph"), [
            {
                data: d1,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#eec446',
                stack: 'other_bars'
            },
            {
                data: d3,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#ff77ff',
                stack: 'other_bars'
            },
            {
                data: d4,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#cb4b4b',
                stack: 'other_bars'
            },
            {
                data: d2,
                lines: { show: true, fill: true },
                points: { show: true },
                color: '#669900',
                stack: 'greengraph'
            },
            {
                data: [[now_position, 0], [now_position, total_points+max_extra_points+5]],
                lines: { show: true, fill: true },
                points: { show: false },
                color: "#888888",
                stack: 'bar'
            }
        ],
        {
            series: {
                stack: true,
                lines: { show: true, fill: true, steps: false },
                bars: { show: false, barWidth: 0.6 }
            },
            xaxis: { ticks: ticks },
            yaxis: { position: "right", labelWidth: 40 },
            grid: { borderWidth: 0},
        });
    }
});


/* Unassigned user storyes (left block) */

var LeftBlockModel = Backbone.Model.extend({
    url: function() {
        return this.get('view').fetch_url();
    }
});

var LeftBlockView = Backbone.View.extend({
    el: $("#backlog-left-block"),

    events: {
        "dragstart .un-us-item": "unassigned_us_dragstart",
        "dragover .uslist-box": "left_block_dragover",
        "dragleave .uslist-box": "left_block_dragleave",
        "drop .uslist-box": "left_block_drop",

        /* Iniline edit */
        "click .un-us-item .config-us-inline": "on_us_edit_inline",
        "click .un-us-item .user-story-inline-submit": "on_us_edit_inline_submit",
        "click .un-us-item .user-story-inline-cancel": "on_us_edit_form_cancel",

        "click .un-us-item .delete": "onUserStoryDeleteClick",

        /* Ordering */
        "click .head-title .row a": "on_order_link_clicked",

        /*Tag filtering */
        "click .category.selected": "on_tag_remove_filter_clicked",
        "click .category.unselected": "on_tag_add_filter_clicked",

        /*Filters box*/
        "click .filters-bar .show-hide-filters-box": "toggle_filters_box_visibility",
        "click .filters-bar .remove-filters": "remove_filters",
        "click .show-hide-graphics a": "toggle_graph_box_visibility"

    },

    initialize: function() {
        _.bindAll(this, 'render', 'reload', 'fetch_url', 'onUserStoryDeleteClick');

        var order_by = getUrlVars()["order_by"];
        if (order_by === undefined){
            this.options.order_by = "-priority";
        }
        else{
            this.options.order_by = order_by;
        }

        this.options.tag_filter = getIntListFromURLParam('tags');

        this.model = new LeftBlockModel({view:this});
        this.model.fetch({success: this.render});
        this.filters_box_visible = false;
    },

    render: function() {
        this.$('.uslist-box').html(this.model.get('html'))
        if (this.filters_box_visible){
            this.$('.filters-box').toggle();
        }
        this.trigger('load');
        Greenmine.main.colorizeTags();
    },

    fetch_url: function() {
        var base_url = this.$el.attr('url');
        var params = "?order_by=" + this.options.order_by;
        params += "&tags=" + this.options.tag_filter;

        if (typeof(window.history.pushState) == 'function'){
            history.pushState({}, "backlog ", params);
        }
        return base_url + params;
    },

    /*
     * Reload state fetching new content from server.
    */

    reload: function() {
        this.model.fetch({success:this.render});
    },

    on_order_link_clicked: function(event) {
        event.preventDefault();
        var self = $(event.currentTarget);

        var order_by = self.attr('order_by');
        var opt_key = "backlog_order_by_" + order_by + "_opt";
        var opt = localStorage.getItem(opt_key)

        if (opt == "" || opt === null) {
            this.options.order_by = order_by;
            localStorage.setItem(opt_key, "-")
        } else {
            this.options.order_by = "-" + order_by;
            localStorage.setItem(opt_key, "");
        }

        this.model.fetch({success:this.render});
    },

    on_tag_add_filter_clicked: function(event) {
        event.preventDefault();
        var self = $(event.currentTarget);
        var tag_filter = parseInt(self.attr('category'));

        if ($.inArray(tag_filter, this.options.tag_filter)<0){
            this.options.tag_filter.push(tag_filter);
            this.model.fetch({success:this.render});
        }
    },

    on_tag_remove_filter_clicked: function(event) {
        event.preventDefault();
        event.stopPropagation();
        var self = $(event.currentTarget).parent();
        var tag_filter = parseInt(self.attr('category'));

        this.options.tag_filter.pop(tag_filter);
        this.model.fetch({success:this.render});
    },

    /*
     * On click to delete button on unassigned user story list.
    */

    onUserStoryDeleteClick: function(event) {
        event.preventDefault();

        var target = $(event.currentTarget);
        var self = this;
        var buttons = {};

        buttons[gettext('Delete')] = function() {
            $(this).dialog('close');
            $.post(target.attr('href'), {}, function(data) {
                target.parents('.un-us-item').remove();
                self.trigger('change');
            });
        };

        buttons[gettext('Cancel')] = function() {
            $(this).dialog('close');
        };

        //TODO: we have no dialogs
        $(".delete-us-dialog").dialog({
            modal: true,
            width: '220px',
            buttons: buttons
        });
    },

    left_block_drop: function(event) {
        var self = $(event.currentTarget);
        if (self.hasClass('drag-over')) {
            self.removeClass('drag-over');
        }

        var source_id = event.originalEvent.dataTransfer.getData('source_id');
        var source = $("#" + source_id);
        var unassign_url = source.attr('unassignurl');
        var $this = this;

        $.post(unassign_url, {}, function(data) {
            self.append(data);
            if(source.parent().find(".us-item").length == 1) {
                source.find(".us-meta").remove()
                source.find(".us-title").html(gettext("No user storys"));
                source.addClass('us-item-empty');
                source.attr('draggable', 'false');
                source.attr('unassignurl', '');
            } else {
                source.remove();
            }

            // Reload some views.
            $this.trigger('change');
            $this.reload();
        }, 'html');

    },

    left_block_dragleave: function(event) {
        var self = $(event.currentTarget);
        if (self.hasClass('drag-over')) {
            self.removeClass('drag-over');
        }
        event.preventDefault();
    },

    left_block_dragover: function(event) {
        var self = $(event.currentTarget);
        event.originalEvent.dataTransfer.dropEffect = 'copy';
        event.preventDefault();
    },

    unassigned_us_dragstart: function(event) {
        var self = $(event.currentTarget);
        event.originalEvent.dataTransfer.effectAllowed = 'copy'; // only dropEffect='copy' will be dropable
        event.originalEvent.dataTransfer.setData('source_id', self.attr('id')); // required otherwise doesn't work
    },

    /*
     * On request visualize a inline edit user story form.
    */

    on_us_edit_inline: function(event) {
        event.preventDefault();
        var self = $(event.currentTarget);
        $.get(self.attr('href'), function(data) {
            self.closest('.un-us-item').find('.form-inline').html(data).show();
        }, 'html');
    },

    /*
     * On inline user story edit form submit changes
    */

    on_us_edit_inline_submit: function(event) {
        event.preventDefault();
        var self = $(event.currentTarget),
            form = self.closest('form'),
            $this = this;

        $.post(form.attr('action'), form.serialize(), function(data) {
            if (data.valid) {
                var usitem = self.closest('.un-us-item');
                usitem.find('.form-inline').hide();

                if (data.action == 'save') {
                    usitem.replaceWith(data.html);
                } else {
                    var ml_id = form.find("#id_milestone").val();
                    var milestone = $("#milestone-" + ml_id);

                    // hide empty entries.
                    milestone.find(".us-item-empty").remove()
                    milestone.find(".milestone-userstorys").append(data.html);
                    usitem.remove();
                }
            } else {
                form.find('.errorlist').remove();
                $.each(data.errors, function(index, value) {
                    var ul = $(document.createElement('ul'))
                        .attr('class', 'errorlist');
                    for(var i=0; i<value.length; i++){
                        $(document.createElement('li')).html(value[i]).appendTo(ul);
                    }

                    form.find('[name='+index+']').before(ul);
                });
            }
            $this.trigger('change');
        }, 'json');

    },
    on_us_edit_form_cancel: function(event) {
        event.preventDefault();
        var self = $(event.currentTarget);
        self.closest('.un-us-item').find('.form-inline').hide();
    },

    toggle_filters_box_visibility: function(event) {
        this.$('.filters-box').toggle();
        this.filters_box_visible = this.$('.filters-box').is(":visible");
    },

    remove_filters: function(event){
        this.options.tag_filter = [];
        this.reload();
    },

    toggle_graph_box_visibility: function(event){
        event.preventDefault();
        this.$('#graphs').toggle();
        this.$('#graphs').toggleClass('visible');
        if (this.$('#graphs').hasClass('visible')){
            $(event.target).text(gettext("Show graphics"));
        }
        else{
            $(event.target).text(gettext("Hide graphics"));
        }
    }

});


/* Milestones (right block) */

var MilestonesModel = Backbone.Model.extend({
    url: function() {
        return this.get('view').$el.attr('url');
    }
});

var RightBlockView = Backbone.View.extend({
    el: $("#backlog-right-block"),

    events: {
        "dragover .milestones .milestone-item": "milestones_dragover",
        "dragleave .milestones .milestone-item": "milestones_drageleave",
        "drop .milestones .milestone-item": "milestones_on_drop",
        "dragstart .milestones .us-item": "milestones_dragstart",

        /* Milestone delete */
        "click .milestone-item .milestone-title a.delete": "on_milestone_delete_click"
    },

    initialize: function() {
        _.bindAll(this, 'render');
        this.model = new MilestonesModel({view:this});
        this.model.on('change', this.render);
        this.model.fetch();
    },

    render: function() {
        var self = this;
        self.$el.html(this.model.get('html'));
        this.trigger('load');
        Greenmine.main.colorizeTags();
    },

    milestones_dragover: function(event) {
        event.originalEvent.dataTransfer.dropEffect = 'copy';
        event.preventDefault();

        var target = $(event.currentTarget);

        if (!target.hasClass("drag-over")) {
            target.addClass("drag-over");
        }
    },

    milestones_drageleave: function(event) {
        event.preventDefault();

        var target = $(event.currentTarget);
        if (target.hasClass('drag-over')) {
            target.removeClass('drag-over');
        }
    },

    milestones_on_drop: function(event) {

        var target = $(event.currentTarget);
        if (target.hasClass('drag-over')) {
            target.removeClass('drag-over');
        }

        var source_id = event.originalEvent.dataTransfer.getData('source_id');
        var source = $("#" + source_id);

        console.log(source_id, source);

        var assign_url = source.attr('assignurl');
        var milestone_id = target.attr('ref');
        var self = this;

        $.post(assign_url, {mid: milestone_id}, function(data) {
            var data_object = $(data);
            target.find(".us-item-empty").remove()
            target.find(".milestone-userstorys").append(data_object);
            source.remove()

            self.trigger('change');
        }, 'html');
    },

    milestones_dragstart: function(event) {
        var self = $(event.currentTarget);
        event.originalEvent.dataTransfer.effectAllowed = 'copy';
        event.originalEvent.dataTransfer.setData('source_id', self.attr('id'));
    },

    on_milestone_delete_click: function(event) {
        event.preventDefault();
        var target = $(event.currentTarget);
        var self = this;
        var buttons = {};

        buttons[gettext('Delete')] = function() {
            $(this).dialog('close');
            $.post(target.attr('href'), {}, function(data) {
                if (data.valid) {
                    target.parents('.milestone-item').remove();
                }
                self.trigger('change');
            }, 'json');
        };

        buttons[gettext('Cancel')] = function() {
            $(this).dialog('close');
        };

        $(".delete-milestone-dialog").dialog({
            modal: true,
            width: '220px',
            buttons: buttons
        });
    }
});

var Backlog = Backbone.View.extend({
    el: $("#backlog"),

    initialize: function() {
        _.bindAll(this, 'render', 'calculateLimit', 'assignedPoints');

        var stats_view = new StatsView();
        var burndown_view = new BurndownView();
        var burnup_view = new BurnupView();

        this.left_block = new LeftBlockView();
        this.right_block = new RightBlockView();

        this.left_block.on('load', this.calculateLimit);
        this.left_block.on('change', stats_view.reload);
        this.left_block.on('change', burndown_view.reload);
        this.left_block.on('change', burndown_view.reload);
        this.left_block.on('change', this.calculateLimit);

        this.right_block.on('load', this.calculateLimit);
        this.right_block.on('change', this.calculateLimit);
        this.right_block.on('change', this.left_block.reload);
        this.right_block.on('change', stats_view.reload);
        this.right_block.on('change', burndown_view.reload);
    },

    assignedPoints: function() {
        var total = 0;
        _.each(this.$(".milestone-userstorys .us-item"), function(item) {
            var points = $(item).find(".us-meta").html();
            if (points === '?') return;

            points = parseFloat(points);
            total += points;
        }, this);

        return total;
    },

    calculateLimit: _.after(2, function(){
        this.$(".limit-line").removeClass("limit-line");

        var items = _.filter(this.$(".un-us-item"), function(item) {
            return !$(item).hasClass("head-title");
        });

        var total_limit = parseFloat(this.$el.attr('total_story_points'));
        if (_.isNaN(total_limit)) {
            return;
        }

        //console.log(total_limit, this.assignedPoints(), total_limit - this.assignedPoints());
        var total_limit = total_limit - this.assignedPoints();

        if (total_limit <= 0) {
            this.$(".head-title").addClass("limit-line");
        } else {
            var total = 0;
            var finished = false;

            _.each(items, function(item) {
                var points = $(item).find(".row.points span").html();
                if (points === '?') return;

                var points = parseFloat(points);
                total += points;

                if (total >= total_limit && !finished) {
                    $(item).addClass("limit-line");
                    finished = true;
                }
            }, this);
        }
    }),

    render: function() {},
});

var backlog = new Backlog();
