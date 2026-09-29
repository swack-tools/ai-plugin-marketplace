const navigation = document.querySelector('.navigation');
const mobileLayout = matchMedia('(max-width: 760px)');
if (navigation) {
  navigation.open = !mobileLayout.matches;
  mobileLayout.addEventListener('change', event => { navigation.open = !event.matches; });
}
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
