function togglePassword(id) {
    const el = document.getElementById("pwd-" + id);
    const isHidden = el.textContent.includes("•");

    if (isHidden) {
        el.textContent = el.getAttribute("data-password");
    } else {
        el.textContent = "••••••••";
    }
}
