<script lang="ts">

	import Search from "$lib/Search.svelte";
  const urlParams = new URLSearchParams(window.location.search);

  / For Search Input
	let searchTerm = "";

  const searchRepos = () => {	
		return filteredRepos = bookData.filter(book => {
			let bookTitle = book.title.toLowerCase();
			return bookTitle.includes(searchTerm.toLowerCase())
		});
	}

</script>

<div class="container relative flex flex-col lg:grid lg:space-y-0 w-full lg:grid-cols-10 md:flex-1 md:grid-rows-full md:gap-6 ">
  <section class="pt-8 border-gray-100 bg-white lg:static lg:px-0 lg:col-span-4 xl:col-span-3 lg:border-r lg:bg-gradient-to-l from-gray-50-to-white hidden lg:block ">
    <div class="mb-4 items-center space-y-3 md:flex md:space-y-0 lg:mb-6">
      <div class="flex items  -center text-lg">
        <h1>Repositories</h1>
      </div>
      <div class="mb-20 lg:mb-4">
        <div class="mb-4 flex items-center justify-between lg:mr-8">
          <div class="relative flex min-w-0 flex-1 items-center">
            <Search />
          </div> 
        </div>
      </div>
    </div>
  </section>
</div>