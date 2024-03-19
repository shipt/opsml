<script lang="ts">

  export let name;
  export let repository;
  export let version;
  export let registry;
  export let date;
  export let color;
  export let defaultClass = `block p-2 mb-2 bg-gradient-to-r from-white from-50% ${color} rounded-2xl w-full border border-black shadow-[-6px_6px_0px_0px_black]`;

  export function calculateDaysBetween(date) {

    let presentDate = new Date();
    let date1 = new Date(date);

    let diff = presentDate.getTime() - date1.getTime();
    let days = Math.round(diff / (1000 * 3600 * 24));

    return days;
  }
    
</script>


<a class={ defaultClass } href="#">
  <header class="flex items-center ml-0.5 mb-0.5" title="{repository}/{name}">
    <h4 class="text-md truncate font-boing text-black text-smd hover:text-primary-600">{repository}/{name}</h4>
  </header>
    
  <div class="mr-1 ml-0.5 flex items-center overflow-hidden whitespace-nowrap text-sm leading-tight text-gray-900">
    <svg class="flex-none w-3 text-gray-900 mr-1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <path fill="#5e0fb7" d="M 12 0 C 5.371094 0 0 5.371094 0 12 C 0 18.628906 5.371094 24 12 24 C 18.628906 24 24 18.628906 24 12 C 24 5.371094 18.628906 0 12 0 Z M 12 2 C 17.523438 2 22 6.476563 22 12 C 22 17.523438 17.523438 22 12 22 C 6.476563 22 2 17.523438 2 12 C 2 6.476563 6.476563 2 12 2 Z M 10.9375 3.875 L 10.5 12.0625 L 10.59375 12.9375 L 16.75 18.375 L 17.71875 17.375 L 12.625 11.96875 L 12.1875 3.875 Z"></path>
    </svg>
    <span class="truncate">Created
      <time date={ date } >
        { calculateDaysBetween(date) } days ago
      </time>
    </span>
    <span class="px-1.5 text-gray-900">- </span>
    <svg class="flex-none w-3 text-gray-900 mr-0.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
      <path fill="#5e0fb7"  d="M8 3a3 3 0 0 0-1 5.83v6.34a3.001 3.001 0 1 0 2 0V15a2 2 0 0 1 2-2h1a5.002 5.002 0 0 0 4.927-4.146A3.001 3.001 0 0 0 16 3a3 3 0 0 0-1.105 5.79A3.001 3.001 0 0 1 12 11h-1c-.729 0-1.412.195-2 .535V8.83A3.001 3.001 0 0 0 8 3Z"/>
    </svg>
    Version: {version}
  </div>
</a>

