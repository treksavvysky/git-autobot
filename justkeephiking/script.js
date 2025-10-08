document.addEventListener('DOMContentLoaded', function() {
    const button = document.getElementById('showTips');
    const tipsContent = document.getElementById('tipsContent');
    
    button.addEventListener('click', function() {
        if (tipsContent.style.display === 'none' || tipsContent.style.display === '') {
            tipsContent.style.display = 'block';
            button.textContent = 'Hide Hiking Tips';
        } else {
            tipsContent.style.display = 'none';
            button.textContent = 'Toggle Hiking Tips';
        }
    });
});