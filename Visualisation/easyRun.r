requiredPackages <- c('shiny','plotly','dplyr','data.table')

for (p in requiredPackages) {
    if (!require(p,character.only=TRUE)) install.packages(p, repos="http://cran.uk.r-project.org")
    suppressMessages(library(p,character.only=TRUE))
}

runApp('../Visualisation', launch.browser=TRUE)
