from nicegui import ui

if __name__ == '__main__':
    ui.dark_mode().enable()

    ui.label('This is in dark mode!')
    ui.button('A dark button', on_click=lambda: ui.label('Lasse er en fucking adam'))

    ui.run(native=True, reload=False)