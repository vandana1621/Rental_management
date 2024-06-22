$(document).ready(function () {
    console.log("Document is ready");

    var calendarEl = document.getElementById('calendar');
    var currentDate = new Date();

    var calendar = new FullCalendar.Calendar(calendarEl, {
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
        },
        initialView: 'dayGridMonth',
        initialDate: currentDate.toISOString().substring(0, 10),
        events: '/get_events/',
        selectable: true,
        selectMirror: true,
        editable: true,
        droppable: true,
        select: function (arg) {
            console.log("Select function called with arg:", arg);

            let startDate = arg.startStr;
            let endDate = arg.endStr ? arg.endStr : arg.startStr;

            console.log("Raw Selected Dates - Start:", startDate, "End:", endDate);

            // Adjust end date if only a single day is selected
            if (!arg.endStr || new Date(endDate).getTime() === new Date(startDate).getTime() + 24 * 60 * 60 * 1000) {
                endDate = startDate;
            }

            console.log("Adjusted Dates - Start:", startDate, "End:", endDate);

            // Validate date selection
            if (!startDate || !endDate) {
                $('#errorMessage').text("Invalid date selection. Please select a valid date range.");
                $('#errorModal').modal('show');
                return;
            }

            // Set dates to hidden fields and log to ensure they are set correctly
            $('#startDate').val(startDate);
            $('#endDate').val(endDate);
            console.log("Form startDate value set to:", $('#startDate').val());
            console.log("Form endDate value set to:", $('#endDate').val());

            if ($('#startDate').val() && $('#endDate').val()) {
                $('#eventModal').modal('show');
            } else {
                console.log("Dates are not set correctly.");
            }
        },
        eventClick: function (info) {
            console.log("Event click function called");

            $('#action').val('READ');
            $('#event_id').val(info.event.id);
            $('#eventVenue').val(info.event.extendedProps.venue);
            $('#clientName').val(info.event.extendedProps.client_name);
            $('#personName').val(info.event.extendedProps.person_name);
            $('#eventModal').modal('show');
        }
    });
    calendar.render();

    $(document).on('click', '#saveEvent', function () {
        console.log("Save button clicked");

        // Validate dates are set
        var startDate = $('#startDate').val();
        var endDate = $('#endDate').val();

        console.log("startdate:", startDate);
        console.log("enddate:", endDate);

        if (!startDate || !endDate) {
            $('#errorMessage').text("Start Date and End Date must be set.");
            $('#errorModal').modal('show');
            return;
        }

        var formData = $('#eventForm').serializeArray();
        formData.push({name: 'start_date', value: startDate});
        formData.push({name: 'end_date', value: endDate});

        console.log("Form Data with dates:", formData);

        $.post("{% url 'add_event_view' %}", formData)
            .done(function (data) {
                console.log("Response Data:", data);
                if (data.success) {
                    $('#eventModal').modal('hide');
                    calendar.refetchEvents();
                } else {
                    $('#errorMessage').text('Error: ' + data.error_message);
                    $('#errorModal').modal('show');
                }
            })
            .fail(function (error) {
                console.error("Error:", error);
                $('#errorMessage').text('An error occurred while saving the event.');
                $('#errorModal').modal('show');
            });
    });
});
