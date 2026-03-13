/* Table Sort JS - Client-side column sorting for ranking tables */

function initTableSort(table) {
    if (table.dataset.sortInitialized) return;
    table.dataset.sortInitialized = 'true';
    var headers = table.querySelectorAll('th[data-sort-key]');
    headers.forEach(function(th) {
        th.addEventListener('click', function() {
            sortTable(table, th);
        });
    });
}

function sortTable(table, th) {
    var tbody = table.querySelector('tbody');
    var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
    var colIndex = Array.prototype.indexOf.call(th.parentNode.children, th);
    var sortType = th.getAttribute('data-sort-type') || 'number';

    // Determine sort direction
    var isAsc = th.classList.contains('sort-desc');
    var allHeaders = table.querySelectorAll('th[data-sort-key]');
    allHeaders.forEach(function(h) {
        h.classList.remove('sort-asc', 'sort-desc');
    });
    th.classList.add(isAsc ? 'sort-asc' : 'sort-desc');

    rows.sort(function(a, b) {
        var cellA = a.children[colIndex];
        var cellB = b.children[colIndex];
        var valA, valB;

        if (sortType === 'string') {
            valA = cellA.textContent.trim();
            valB = cellB.textContent.trim();
            var cmp = valA.localeCompare(valB);
            return isAsc ? cmp : -cmp;
        }

        // Numeric: use data-sort-value if present, otherwise parse text
        valA = cellA.hasAttribute('data-sort-value')
            ? parseFloat(cellA.getAttribute('data-sort-value'))
            : parseFloat(cellA.textContent);
        valB = cellB.hasAttribute('data-sort-value')
            ? parseFloat(cellB.getAttribute('data-sort-value'))
            : parseFloat(cellB.textContent);

        if (isNaN(valA)) valA = -Infinity;
        if (isNaN(valB)) valB = -Infinity;

        return isAsc ? valA - valB : valB - valA;
    });

    // Re-append sorted rows and update rank numbers
    rows.forEach(function(row, i) {
        tbody.appendChild(row);
        row.children[0].textContent = i + 1;
    });
}
