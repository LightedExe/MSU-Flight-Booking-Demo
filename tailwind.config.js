/** @type {import('tailwindcss').Config} */
module.exports = {
	content: ["./templates/**/*.{html,js}"],
	theme: {
		extend: {
			colors: {
				'proj-white': '#EEEEEE',
				'proj-blue': '#00ADB5',
				'proj-gray': '#393E46',
				'proj-black': '#222831',
			},
			fontFamily: {
				'tangerine': ['Tangerine', 'cursive'],
				'comfortaa': ['Comfortaa', 'sans-serif']
			  },
		},
	},
	plugins: [],
}

