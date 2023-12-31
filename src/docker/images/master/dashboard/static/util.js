function openTab(e, tabName) {
    switch (tabName) {
        case "plotsPage":
            window.location.replace("dashboard");
            return;
        case "tablePage":
            window.location.replace("table");
            return;
        case "carbonDataPage":
            window.location.replace("carbonData");
            return;
        default:
            return;
    }   
}