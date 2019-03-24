function openNav() {
    is_coarse = matchMedia('(pointer:coarse)').matches
    if (is_coarse) {
        document.getElementById("mySidenav").style.width = "100%";
    } else {
        document.getElementById("mySidenav").style.width = "200px";
    }

}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    // document.getElementById("wrapper").style.marginLeft= "auto";
}
