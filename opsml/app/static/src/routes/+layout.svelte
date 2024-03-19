<script>
  import "../app.css";
  import Navbar from '$lib/Navbar.svelte';
  import Footer from '$lib/Footer.svelte';
  import favicon from '$lib/images/opsml-green.ico';

</script>

<svelte:head>
  <link rel="icon" type="image/x-icon" href={favicon} />
</svelte:head>

<div class="layout overflow-auto">
    <Navbar />
    <div class="image"></div>
    <slot></slot>
</div>



<style>
  .image {
    position: absolute;
    width: 100%;
    height: 100%;
    background-image: url("$lib/images/opsml-background.svg");
    z-index: -1;
  }
</style>