from nicegui import ui

ui.dark_mode().enable()

ui.label('This is in dark mode!')
ui.button('A dark button')

ui.run(native=True)