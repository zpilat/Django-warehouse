// Funkce pro načtení formulářů (vytvořit/upravit/smazat) do pravého sloupce
function loadForm(url) {
    fetch(url)
    .then(response => response.text())
    .then(html => {
        document.getElementById('detail').innerHTML = html;
    })
    .catch(err => console.error('Chyba při načítání formuláře:', err));
}

document.addEventListener("DOMContentLoaded", function() {
    function loadDetail(url, evidencniCislo) {
        fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('detail').innerHTML = html;
            // Aktualizace URL a zvýraznění řádku
            history.pushState(null, '', '?selected=' + evidencniCislo);
            document.querySelectorAll('tr').forEach(row => {
                row.classList.remove('selected-row');
            });
            document.querySelector('tr[data-evidencni-cislo="' + evidencniCislo + '"]').classList.add('selected-row');
        })
        .catch(err => console.error('Chyba při načítání detailů:', err));
    }

    function selectFirstRow() {
        const firstRow = document.querySelector('table tbody tr:nth-child(1)'); // První řádek v těle tabulky
        if (firstRow) {
            const evidencniCislo = firstRow.getAttribute('data-evidencni-cislo');
            const detailUrl = firstRow.getAttribute('data-detail-url');
            loadDetail(detailUrl, evidencniCislo);
        }
    }

    // Automaticky vyberte první řádek při načtení stránky
    selectFirstRow();    

    // Přidání onclick události ke všem řádkům
    document.querySelectorAll('table tbody tr').forEach(row => {
        row.addEventListener('click', function() {
            const evidencniCislo = this.getAttribute('data-evidencni-cislo');
            const detailUrl = this.getAttribute('data-detail-url');
            loadDetail(detailUrl, evidencniCislo);
        });
    });

    // Přidání onclick události k odkazům, které načítají formuláře
    document.querySelectorAll('a[data-load-form]').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const url = this.getAttribute('href');
            loadForm(url);
        });
    });
});
