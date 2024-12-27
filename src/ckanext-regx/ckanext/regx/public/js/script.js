$(document).ready(function () {
    $('#profilesTable').DataTable({
        paging: true,
        searching: true,
        ordering: true,
        info: true,
        lengthChange: true,
        columns: [
            { title: "ID" },
            { title: "Name" },
            { title: "Email" },
            { title: "Role" },
            { title: "Status" },
            { title: "Actions" }
        ]
    });
});
