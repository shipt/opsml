<script>
  import "../app.css";
  import Navbar from "$lib/Navbar.svelte";
  import favicon from "$lib/images/opsml-green.ico";
  import background from "$lib/images/opsml-gradient-background.svg";

</script>

<svelte:head>
  <link rel="icon" type="image/x-icon" href={favicon}/>
</svelte:head>

<div class="bg-cover bg-center layout overflow-auto" style="background-image: url({background})" id="page">
    <Navbar />
    <slot></slot>
</div>
