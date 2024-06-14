document.addEventListener("DOMContentLoaded", function() {
    function loadDetail(url, id) {
        fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('detail').innerHTML = html;
            // Aktualizace URL a zvýraznění řádku
            history.pushState(null, '', '?selected=' + id);
            document.querySelectorAll('tr').forEach(row => {
                row.classList.remove('table-info');
            });
            document.querySelector('tr[data-id="' + id + '"]').classList.add('table-info');
        })
        .catch(err => console.error('Chyba při načítání detailů:', err));
    }

    function selectFirstRow() {
        const firstRow = document.querySelector('table tbody tr:first-child'); // První řádek v těle tabulky
        if (firstRow) {
            const id = firstRow.getAttribute('data-id');
            const detailUrl = firstRow.getAttribute('data-detail-url');
            loadDetail(detailUrl, id);
        }
    }

    // Automaticky vyberte první řádek při načtení stránky
    selectFirstRow();

    // Přidání onclick události ke všem řádkům
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const detailUrl = this.getAttribute('data-detail-url');
            loadDetail(detailUrl, id);
        });
    });
});

