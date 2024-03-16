<script>
    import Navbar from '$lib/Navbar.svelte';
    import Footer from '$lib/Footer.svelte';
</script>

<div class="layout">
    <Navbar />
    <slot />
    <Footer />
</div>