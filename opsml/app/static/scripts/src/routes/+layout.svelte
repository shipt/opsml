<script>
    import "../app.css";
    import Navbar from '$lib/Navbar.svelte';
    import Footer from '$lib/Footer.svelte';
    import favicon from '$lib/images/favicon.svg';
</script>

<svelte:head>
  <link rel="icon" type="image/svg" href={favicon} />
</svelte:head>

<div class="layout">
    <Navbar />
    <slot />
    <Footer />
</div>