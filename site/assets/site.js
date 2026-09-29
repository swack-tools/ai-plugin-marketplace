const navigation = document.querySelector('.navigation');
if (navigation && matchMedia('(max-width: 760px)').matches) navigation.open = false;
for (const button of document.querySelectorAll('.copy')) {
  if (!navigator.clipboard) continue;
  button.hidden = false;
  button.addEventListener('click', async () => {
    const text = button.closest('.example').querySelector('pre code').textContent;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = 'Copied';
      setTimeout(() => { button.textContent = 'Copy'; }, 1600);
    } catch { button.textContent = 'Select text to copy'; }
  });
}
