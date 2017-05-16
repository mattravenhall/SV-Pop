requiredPackages <- c('shiny','plotly','dplyr','data.table')

for (p in requiredPackages) {
    if (!require(p,character.only=TRUE)) install.packages(p)
    suppressMessages(library(p,character.only=TRUE))
}

runApp('../shinyTest', launch.browser=TRUE)
