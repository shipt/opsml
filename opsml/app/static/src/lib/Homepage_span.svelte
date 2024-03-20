<script lang="ts">

  export let logo: string;
  export let header: string;

</script>

<div class="relative col-span-1 flex flex-col items-stretch text-center">
  <h2 class="mb-5 flex items-center justify-center  text-lg font-semibold 2xl:mb-6 2xl:text-xl">
    <img src={logo} class="w-24" alt="">
    {header}
  </h2>
  <div class="mb-3 flex flex-col items-center gap-2.5 rounded-xl bg-white/40 p-3 backdrop-blur-lg sm:mb-7">
    <slot></slot>
  </div>
</div>